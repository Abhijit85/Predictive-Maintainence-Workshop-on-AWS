"""Tests for stream.py — SNS alerting and stream_prediction logic (all I/O mocked)."""

import pytest
from unittest.mock import patch, MagicMock, call


# ── publish_alert ────────────────────────────────────────────────────

class TestPublishAlert:
    @patch("stream.sns_client")
    @patch("stream.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:alerts")
    def test_publishes_when_configured(self, mock_sns):
        from stream import publish_alert
        publish_alert("Critical Alert", "Something broke")
        mock_sns.publish.assert_called_once_with(
            TopicArn="arn:aws:sns:us-east-1:123:alerts",
            Subject="Critical Alert",
            Message="Something broke"
        )

    @patch("stream.sns_client", None)
    @patch("stream.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:alerts")
    def test_noop_when_no_client(self):
        from stream import publish_alert
        # Should not raise
        publish_alert("Alert", "msg")

    @patch("stream.sns_client")
    @patch("stream.SNS_TOPIC_ARN", "")
    def test_noop_when_no_arn(self, mock_sns):
        from stream import publish_alert
        publish_alert("Alert", "msg")
        mock_sns.publish.assert_not_called()

    @patch("stream.sns_client")
    @patch("stream.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:alerts")
    def test_truncates_long_subject(self, mock_sns):
        from stream import publish_alert
        long_subject = "A" * 200
        publish_alert(long_subject, "msg")
        actual_subject = mock_sns.publish.call_args[1]["Subject"]
        assert len(actual_subject) <= 100

    @patch("stream.sns_client")
    @patch("stream.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:alerts")
    def test_handles_publish_error_gracefully(self, mock_sns):
        mock_sns.publish.side_effect = Exception("Throttled")
        from stream import publish_alert
        # Should not raise
        publish_alert("Alert", "msg")


# ── stream_prediction (core loop logic) ──────────────────────────────

class TestStreamPrediction:
    @patch("stream.publish_alert")
    @patch("stream.requests")
    def test_inserts_and_alerts_on_critical(self, mock_requests, mock_alert):
        """Simulate a change stream insert → API call → DB insert → SNS alert."""
        from stream import stream_prediction

        # Mock the API response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "encoded_prediction": 1,
            "model_used": "Random_Forest-valve_condition",
            "prediction": 4  # critical value
        }
        mock_requests.post.return_value = mock_resp

        # Mock the change stream to yield one event then stop
        mock_change = {
            "fullDocument": {"sensor_1": 100, "sensor_2": 200}
        }

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=iter([mock_change]))
        mock_stream.__exit__ = MagicMock(return_value=False)

        source_col = MagicMock()
        source_col.full_name = "db.input_col"
        source_col.watch.return_value = mock_stream

        description_col = MagicMock()
        description_col.find_one.return_value = {
            "description": "Critical failure",
            "color": "#dc3545",
            "icon": "X"
        }

        target_col = MagicMock()
        target_col.full_name = "db.output_col"

        stream_prediction(
            "http://localhost:5001",
            "Random_Forest-valve_condition",
            source_col, description_col, target_col
        )

        # Verify target insert was called
        target_col.insert_one.assert_called_once()
        inserted_doc = target_col.insert_one.call_args[0][0]
        assert inserted_doc["color"] == "#dc3545"
        assert inserted_doc["description"] == "Critical failure"

        # Verify SNS alert was triggered
        mock_alert.assert_called_once()
        alert_subject = mock_alert.call_args[0][0]
        assert "Critical" in alert_subject

    @patch("stream.publish_alert")
    @patch("stream.requests")
    def test_no_alert_for_non_critical(self, mock_requests, mock_alert):
        """Non-critical predictions should not trigger SNS alerts."""
        from stream import stream_prediction

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "encoded_prediction": 0,
            "model_used": "RF-test",
            "prediction": 1
        }
        mock_requests.post.return_value = mock_resp

        mock_change = {"fullDocument": {"s1": 50}}

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=iter([mock_change]))
        mock_stream.__exit__ = MagicMock(return_value=False)

        source_col = MagicMock()
        source_col.full_name = "db.input"
        source_col.watch.return_value = mock_stream

        description_col = MagicMock()
        description_col.find_one.return_value = {
            "description": "Normal",
            "color": "#28a745",
            "icon": "OK"
        }

        target_col = MagicMock()
        target_col.full_name = "db.output"

        stream_prediction("http://localhost:5001", "RF-test", source_col, description_col, target_col)

        target_col.insert_one.assert_called_once()
        mock_alert.assert_not_called()
