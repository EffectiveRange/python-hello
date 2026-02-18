from context_logger import get_logger, setup_logging

from examples import setup_shutdown
from hello import Hello, Group, ServiceQuery, DiscoveryEvent

setup_logging('hello')

log = get_logger('CameraDiscovery')


def main() -> None:
    shutdown_event = setup_shutdown()

    # Define the group to discover camera services on
    group = Group(name='effective-range/sniper', url='udp://239.0.1.1:5555')

    # Define the query to discover matching camera services
    query = ServiceQuery(name='.+', role='camera')

    # Use a discoverer to find camera services
    with Hello.builder().discoverer().default() as discoverer:
        # Define an event handler to process discovery events
        def process_event(event: DiscoveryEvent) -> None:
            log.info('Service discovery event', type=event.type.name, service=event.service)

        # Register the event handler
        discoverer.register(process_event)

        # Start the discoverer with the specified group
        discoverer.start(group)

        # Send a service query to trigger advertisement from matching services
        discoverer.discover(query)

        shutdown_event.wait()


if __name__ == '__main__':
    main()
