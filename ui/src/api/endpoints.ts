const HOST = process.env.REACT_APP_FASTAPI_HOST;
const PORT = process.env.REACT_APP_FASTAPI_PORT || "5001";
const HOST_SERVER = HOST ? `http://${HOST}${PORT === "80" ? "" : `:${PORT}`}` : "";
const API_KEY = process.env.REACT_APP_API_KEY || "";

export enum EndpointsAction {
    SENSORS = "sensors",
    MONITORING = "monitoring",
    DIAGNOSE = "diagnose"
}

export const endpointsMap = {
    sensors: {
        path: `${HOST_SERVER}/api/sensors`,
        config: {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": API_KEY,
            }
        }
    },
    monitoring: {
        path: `${HOST_SERVER}/api/monitoring`,
        config: {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": API_KEY,
            }
        }
    },
    diagnose: {
        path: `${HOST_SERVER}/api/diagnose`,
        config: {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": API_KEY,
            }
        }
    }
};
