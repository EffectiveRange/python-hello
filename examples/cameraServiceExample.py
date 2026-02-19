from uuid import uuid4

from context_logger import get_logger, setup_logging

from examples import setup_shutdown
from hello import ServiceInfo, Hello, Group, GroupUrl

setup_logging('hello')

log = get_logger('CameraService')


def main() -> None:
    shutdown_event = setup_shutdown()

    # Define the group URL optionally specifying the network interface
    url = GroupUrl(address='239.0.1.1', port=5555, interface='wlan0')

    # Define the group to advertise the camera service on
    group = Group.create(name='effective-range/sniper', url=url)

    # Define the service information for the camera
    hostname = 'er-sniper-camera-1'
    info = ServiceInfo(uuid=uuid4(), name=hostname, role='camera', urls={
        'api': f'grpc://{hostname}.local:50051',
        'stream': f'http://{hostname}.local:8000'
    })

    # Use a scheduled advertizer to periodically announce the camera service
    with Hello.builder().advertizer().scheduled() as advertizer:
        # Start the advertizer with the specified group
        advertizer.start(group)

        # Immediately advertise the service information
        advertizer.advertise(info)

        # Schedule periodic advertisements every 10 seconds
        advertizer.schedule_periodic(interval=10)

        shutdown_event.wait()


if __name__ == '__main__':
    main()
