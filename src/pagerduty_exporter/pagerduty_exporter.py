import time
from flask import Flask, Response

from pdpyras import APISession
from prometheus_client import Gauge, CollectorRegistry, generate_latest

registry = CollectorRegistry()
api_token = 'token_here'
session = APISession(api_token)
service_ids = [
    'XXXXX',
    'YYYYY'
]
statuses = (
    'triggered',
    'acknowledged'
)


def on_call_data():
    return session.list_all('oncalls')


def get_generic_data(item_type, params):
    if params:
        return session.dict_all(item_type, params=params)
    else:
        return session.dict_all(item_type)


def active_incident_data():
    params = {'statuses[]': statuses, 'service_ids[]': service_ids}
    return get_generic_data('incidents', params)


def get_user_data():
    return get_generic_data('users')


def schedule_data():
    return get_generic_data('schedules')


def service_data():
    return get_generic_data('services')


def escalation_policy_data():
    return get_generic_data('escalation_policies')


def active_maintenance_window_data():
    params = {'filter': 'ongoing'}
    return get_generic_data('maintenance_windows', params)


def cleanup_incident_info():
    print("getting data")
    cleaned_up_incident_data = []
    for key_item, data in active_incident_data().items():
        temp_dict = {
            'title': data['title'],
            'id': key_item,
            'status': data['status'],
            'service': data['service']['summary'],
            'urgency': data['urgency']
        }
        cleaned_up_incident_data.append(temp_dict)
    return cleaned_up_incident_data


incident_info_gauge = Gauge('incident_info', 'pagerduty incident information',
                            ('status', 'service', 'urgency', 'title', 'id'))

my_app = Flask(__name__)


@my_app.route('/metrics', methods=['GET'])
def get_data():
    for item in cleanup_incident_info():
        incident_info_gauge.labels(**item).set(1)
    return Response(generate_latest(), mimetype='text/plain')


my_app.run(host='0.0.0.0', port=8080)
