from prometheus_client import start_http_server, Gauge, CollectorRegistry, REGISTRY

registry = CollectorRegistry()

edgeos_network_receive_bytes_total = Gauge(
    'edgeos_network_receive_bytes_total',
    'Network device statistic receive_bytes',
    ['interface'],
    registry=registry)

edgeos_network_receive_drop_total = Gauge(
    'edgeos_network_receive_drop_total',
    'Network device statistic receive_drop.',
    ['interface'],
    registry=registry)

edgeos_network_receive_errs_total = Gauge(
    'node_network_receive_errs_total',
    'Network device statistic receive_errs.',
    ['interface'],
    registry=registry)

edgeos_network_receive_packets_total = Gauge(
    'edgeos_network_receive_packets_total',
    'Network device statistic receive_packets.',
    ['interface'],
    registry=registry)

edgeos_network_receive_speed_bps = Gauge(
    'edgeos_network_receive_speed_bps',
    'Network device receive speed bps',
    ['interface'],
    registry=registry)

edgeos_network_transmit_bytes_total = Gauge(
    'edgeos_network_transmit_bytes_total',
    'Network device statistic transmit_bytes',
    ['interface'],
    registry=registry)

edgeos_network_transmit_drop_total = Gauge(
    'edgeos_network_transmit_drop_total',
    'Network device statistic transmit_drop.',
    ['interface'],
    registry=registry)

edgeos_network_transmit_errs_total = Gauge(
    'node_network_transmit_errs_total',
    'Network device statistic transmit_errs.',
    ['interface'],
    registry=registry)

edgeos_network_transmit_packets_total = Gauge(
    'edgeos_network_transmit_packets_total',
    'Network device statistic transmit_packets.',
    ['interface'],
    registry=registry)

edgeos_network_transmit_speed_bps = Gauge(
    'edgeos_network_transmit_speed_bps',
    'Network device transmit speed bps',
    ['interface'],
    registry=registry)

edgeos_network_multicast_total = Gauge(
    'edgeos_network_multicast_total',
    'Network device statistic multicast.',
    ['interface'],
    registry=registry)

edgeos_system_cpu = Gauge(
    'edgeos_system_cpu',
    'System CPU Utilisation',
    registry=registry)

edgeos_system_uptime = Gauge(
    'edgeos_system_uptime',
    'System  Uptime',
    registry=registry)

edgeos_system_mem = Gauge(
    'edgeos_system_mem',
    'System Memory Utilisation',
    registry=registry)


def start_server(port=None):

    if port and port.isnumeric():
        prometheus_export_port = port
    else:
        prometheus_export_port = 9788

    start_http_server(prometheus_export_port)
    REGISTRY.register(registry)


def register_edgeos_metrics(metrics: dict):

    if interfaces := metrics.get('interfaces'):
        for iface_name, iface_data in interfaces.items():

            edgeos_network_receive_bytes_total.labels(iface_name).set(iface_data['stats']['rx_bytes'])
            edgeos_network_receive_drop_total.labels(iface_name).set(iface_data['stats']['rx_dropped'])
            edgeos_network_receive_errs_total.labels(iface_name).set(iface_data['stats']['rx_errors'])
            edgeos_network_receive_packets_total.labels(iface_name).set(iface_data['stats']['rx_packets'])
            edgeos_network_receive_speed_bps.labels(iface_name).set(iface_data['stats']['rx_bps'])

            edgeos_network_transmit_bytes_total.labels(iface_name).set(iface_data['stats']['tx_bytes'])
            edgeos_network_transmit_drop_total.labels(iface_name).set(iface_data['stats']['tx_dropped'])
            edgeos_network_transmit_errs_total.labels(iface_name).set(iface_data['stats']['tx_errors'])
            edgeos_network_transmit_packets_total.labels(iface_name).set(iface_data['stats']['tx_packets'])
            edgeos_network_transmit_speed_bps.labels(iface_name).set(iface_data['stats']['tx_bps'])

            edgeos_network_multicast_total.labels(iface_name).set(iface_data['stats']['multicast'])

    if system_stats := metrics.get('system-stats'):

        edgeos_system_cpu.set(system_stats['cpu'])
        edgeos_system_uptime.set(system_stats['uptime'])
        edgeos_system_mem.set(system_stats['mem'])
