import os
import sys
import argparse
import configparser
from time import sleep
from led_controller import LEDController
from current_spotify_playback import CurrentSpotifyPlayback
from spotify_background_color import SpotifyBackgroundColor


CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI')
REFRESH_TOKEN = os.environ.get('SPOTIPY_REFRESH_TOKEN')


def main(k, color_tol, size):
    """Sets the LED-strip to a suitable color for the current artwork.

    Args:
        k (int): Number of clusters to form.
        color_tol (float): Tolerance for a colorful color.
            Colorfulness is defined as described by Hasler and
            Süsstrunk (2003) in https://infoscience.epfl.ch/record/
            33994/files/HaslerS03.pdf.
        size: (int/float/tuple): Process image or not.
            int - Percentage of current size.
            float - Fraction of current size.
            tuple - Size of the output image.

    """
    config = configparser.ConfigParser()
    config.read('config.ini')
    GPIO_PINS = config['GPIO PINS']
    red_pin = int(GPIO_PINS['red_pin'])
    green_pin = int(GPIO_PINS['green_pin'])
    blue_pin = int(GPIO_PINS['blue_pin'])
    name = config['CHROMECAST']['name']

    led = LEDController(red_pin, green_pin, blue_pin)
    spotify = CurrentSpotifyPlayback(CLIENT_ID, CLIENT_SECRET,
                                     REDIRECT_URI, REFRESH_TOKEN)

    old_song_id = ''
    try:
        while True:
            spotify.update_current_playback()
            if spotify.connected_to_chromecast(name):
                if spotify.new_song(old_song_id):
                    artwork = spotify.get_artwork()
                    background_color = SpotifyBackgroundColor(
                        img=artwork, image_processing_size=size)
                    r, g, b = background_color.best_color(
                        k=k, color_tol=color_tol)
                    led.set_color(r, g, b)
                    old_song_id = spotify.get_current_song_id()
            else:
                old_song_id = ''
                r, g, b = led.get_color()
                if r != 0 or g != 0 or b != 0:
                    led.set_color(0, 0, 0)
            sleep(2)
    except KeyboardInterrupt:
        led.set_color(0, 0, 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runs the Spotify '\
                                    'background color script')
    parser.add_argument('-k', '--cluster', metavar='NUMBER', type=int,
                        default=8, help='number of clusters used in '\
                        'the k-means clustering')
    parser.add_argument('-t', '--tol', metavar='TOLERANCE', type=float,
                        default=0, help='tolerance for a colorful color')
    parser.add_argument('-s', '--size', metavar='SIZE', type=int, nargs='+',
                        default=(100, 100), help='artwork width and height to use')

    args = parser.parse_args()
    main(args.cluster, args.tol, tuple(args.size))