import os
import sys
import json
import subprocess
import argparse
import logging
import tempfile
import shutil

if getattr(sys, 'frozen', False):
    DIRECTORY = '/app'
else:
    DIRECTORY = os.path.dirname(os.path.abspath(__file__))

TF_DIR = f'{DIRECTORY}/terraform'
TF_PLAN_FILE = f'{TF_DIR}/plan'
TF_CONFIG_DIR = f'{TF_DIR}/config/config.tfvars.json'
UI_DIR = f'{DIRECTORY}/ui'

LOGS_PATH = '/output/app.log'

if not os.path.exists('/output'):
    os.makedirs('/output')
    os.chmod('/output', 0o777)

if not os.path.exists(LOGS_PATH):
    with open(LOGS_PATH, 'w') as f:
        pass
    os.chmod(LOGS_PATH, 0o777)


class FunctionFailed(Exception):
    pass

def terraform_init():
    logging.info('Initializing Terraform infrastructure.')
    logging.debug(f'Terraform will be initialized in the directory: {TF_DIR}')

    result = subprocess.run(['terraform', f'-chdir={TF_DIR}', 'init'], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error('Terraform initialization failed.')
        raise FunctionFailed()

    logging.debug(result.stdout)

def terraform_apply(action):
    logging.info('Executing terraform apply.')
    command = ['terraform', f'-chdir={TF_DIR}', 'apply', TF_PLAN_FILE]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
         line_clean = line.rstrip()
         logging.info(line_clean)

    process.wait()

    if process.returncode != 0:
        logging.error(f'Terraform {action} failed.')
        raise FunctionFailed()

def terraform_plan(action):
    logging.debug(f'Executing terraform plan with config file {TF_PLAN_FILE}')
    command = ['terraform', f'-chdir={TF_DIR}', 'plan', f'--var-file={TF_CONFIG_DIR}', '-out', TF_PLAN_FILE]

    if action == 'destroy':
        command.insert(3, '--destroy')

    logging.debug(f'Exporting terraform plan output to {TF_PLAN_FILE}')
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    no_changes = False

    for line in process.stdout:
         line_clean = line.rstrip()
         logging.info(line_clean) if action == 'plan' else logging.debug(line_clean)

         if 'No changes' in line_clean:
             no_changes = True

    process.wait()

    if process.returncode != 0:
        logging.error('Terraform plan failed.')
        raise FunctionFailed()

    if action == 'plan':
        return

    if no_changes:
        if action == 'apply':
            logging.error('Error in \'apply\' action. No changes detected in the infrastructure configuration.')
        else:
            logging.error('Error in \'destroy\' action. No resources found to delete.')
        raise FunctionFailed()

def terraform_output(name):
    result = subprocess.run(
        ['terraform', f'-chdir={TF_DIR}', 'output', '-raw', name],
        capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ''

def get_aws_region():
    """Return the AWS region from environment, checking both common variable names."""
    return os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION') or 'us-east-1'

def deploy_frontend():
    amplify_app_id = terraform_output('amplify_app_id')
    amplify_app_url = terraform_output('amplify_app_url')

    if not amplify_app_id:
        logging.warning('Amplify app ID not found in Terraform outputs. Skipping frontend deployment.')
        return

    if not os.path.isdir(UI_DIR):
        logging.warning(f'UI source directory not found at {UI_DIR}. Skipping frontend deployment.')
        return

    region = get_aws_region()
    logging.info(f'Building frontend UI (Amplify app: {amplify_app_id}, region: {region}).')

    # Install dependencies
    result = subprocess.run(
        ['npm', 'ci', '--prefer-offline'],
        cwd=UI_DIR, capture_output=True, text=True
    )
    if result.returncode != 0:
        logging.error(f'npm install failed: {result.stderr}')
        raise FunctionFailed()

    # Build with empty host so UI uses relative URLs
    # Amplify proxy rules route /api/* through CloudFront to the ALB
    env = os.environ.copy()
    env.pop('REACT_APP_FASTAPI_HOST', None)
    env.pop('REACT_APP_FASTAPI_PORT', None)

    result = subprocess.run(
        ['npm', 'run', 'build'],
        cwd=UI_DIR, capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        logging.error(f'React build failed: {result.stderr}')
        raise FunctionFailed()

    build_dir = os.path.join(UI_DIR, 'build')
    if not os.path.isdir(build_dir):
        logging.error('React build directory not found after build.')
        raise FunctionFailed()

    # Create zip of build contents
    zip_path = os.path.join(tempfile.gettempdir(), 'ui-build.zip')
    result = subprocess.run(
        ['zip', '-r', zip_path, '.'],
        cwd=build_dir, capture_output=True, text=True
    )
    if result.returncode != 0:
        logging.error(f'Failed to create zip: {result.stderr}')
        raise FunctionFailed()

    # Create Amplify deployment
    logging.info(f'Deploying frontend to Amplify app {amplify_app_id}.')

    result = subprocess.run(
        ['aws', 'amplify', 'create-deployment',
         '--app-id', amplify_app_id,
         '--branch-name', 'main',
         '--region', region],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        logging.error(f'Amplify create-deployment failed: {result.stderr}')
        raise FunctionFailed()

    try:
        deploy_info = json.loads(result.stdout)
        job_id = deploy_info['jobId']
        upload_url = deploy_info['zipUploadUrl']
    except (json.JSONDecodeError, KeyError) as e:
        logging.error(f'Failed to parse Amplify deployment response: {e}')
        logging.error(f'Raw output: {result.stdout[:500]}')
        raise FunctionFailed()

    # Upload zip
    result = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-T', zip_path, upload_url],
        capture_output=True, text=True
    )
    if result.returncode != 0 or result.stdout.strip() not in ('200', '204'):
        logging.error(f'Amplify zip upload failed (HTTP {result.stdout.strip()}): {result.stderr}')
        raise FunctionFailed()

    # Start deployment
    result = subprocess.run(
        ['aws', 'amplify', 'start-deployment',
         '--app-id', amplify_app_id,
         '--branch-name', 'main',
         '--job-id', job_id,
         '--region', region],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        logging.error(f'Amplify start-deployment failed: {result.stderr}')
        raise FunctionFailed()

    # Clean up
    os.remove(zip_path)
    shutil.rmtree(build_dir, ignore_errors=True)

    frontend_url = amplify_app_url or f'https://main.{amplify_app_id}.amplifyapp.com'
    logging.info(f'Frontend deployed successfully: {frontend_url}')

def generate_terraform_config():
    logging.info('Generating one click configuration.')
    logging.debug(f'Exporting config to {TF_CONFIG_DIR}')

    with open(TF_CONFIG_DIR, 'w') as f:
        subprocess.run(
            ['terraform-docs', 'tfvars', 'json', TF_DIR],
            stdout=f,
            check=True
        )

    os.chmod(TF_CONFIG_DIR, 0o777)
    logging.info('Configuration successfully generated.')

parser = argparse.ArgumentParser(
    description='Predictive Maintenance One Click Deployment CLI')
parser.add_argument('action', choices=['apply', 'destroy', 'generate-config', 'plan'],
                    help='Specify CLI operation.')
parser.add_argument('--debug', action='store_true',
                    help='Enables debug log level.')

args = parser.parse_args()

log_level = logging.DEBUG if args.debug else logging.INFO

formatter = logging.Formatter(
    '{asctime} - {levelname} - {message}', style='{', datefmt='%Y-%m-%d %H:%M'
)

logging.getLogger().setLevel(log_level)

file_handler = logging.FileHandler(LOGS_PATH, mode='a')
file_handler.setFormatter(formatter)
logging.getLogger().addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)


def main():
    action = args.action

    # Generate config try/except block
    try:
        if action == 'generate-config':
            generate_terraform_config()
            sys.exit(0)

    except subprocess.CalledProcessError:
        logging.error('Config generation failed.')
        sys.exit(1)

    # Main try/except block
    try:
        logging.info(f'Executing {action} action.')

        terraform_init()
        terraform_plan(action)

        if action != 'plan':
            terraform_apply(action)

        if action == 'apply':
            deploy_frontend()

    except FunctionFailed:
        exit_code = 1
    else:
        exit_code = 0

    finally:
        sys.exit(exit_code)

if __name__ == "__main__":
    main()
