from uuid import uuid4

from common_utility import InterfaceResolver
from context_logger import get_logger, setup_logging

from examples import setup_shutdown
from hello import Service, Hello, Group

setup_logging('hello')

log = get_logger('CameraService')


def main() -> None:
    shutdown_event = setup_shutdown()

    # Resolve the address for the specified interface name (e.g., 'wlan0')
    if_address = InterfaceResolver().resolve('wlan0')

    # Define the group to advertise the camera service on
    group = Group.create(name='effective-range/sniper', address='239.0.1.1', port=5555, if_address=if_address)

    # Define the service information for the camera
    service = Service(uuid=uuid4(), name='er-sniper-camera-1', role='camera', address=if_address, urls={
        'api': f'grpc://{if_address}:50051',
        'stream': f'http://{if_address}:8000/video_feed'
    })

    # Use a scheduled advertizer to periodically announce the camera service
    with Hello.builder().advertizer().scheduled() as advertizer:
        # Start the advertizer with the specified group
        advertizer.start(group)

        # Immediately advertise the service information
        advertizer.advertise(service)

        # Schedule periodic advertisements every 10 seconds
        advertizer.schedule_periodic(interval=10)

        shutdown_event.wait()


if __name__ == '__main__':
    main()
