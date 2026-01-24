from context_logger import get_logger, setup_logging

from examples import setup_shutdown
from hello import ServiceInfo, Hello, Group

setup_logging('hello')

log = get_logger('CameraService')


def main() -> None:
    shutdown_event = setup_shutdown()

    # Define the group to advertise the camera service on
    group = Group(name='effectiverange/sniper', url='udp://239.0.1.1:5555')

    # Define the service information for the camera
    info = ServiceInfo(name='er-sniper-camera-1', role='camera', urls={
        'device-api': 'grpc://er-sniper-camera-1/device',
        'video-stream': 'blob:http://er-sniper-camera-1/video'
    })

    # Use a scheduled advertizer to periodically announce the camera service
    with Hello.builder().advertizer().scheduled() as advertizer:
        # Start the advertizer with the specified group
        advertizer.start(group)

        # Immediately advertise the service information
        advertizer.advertise(info)

        # Schedule periodic advertisements every 10 seconds
        advertizer.schedule(interval=10)

        shutdown_event.wait()


if __name__ == '__main__':
    main()
