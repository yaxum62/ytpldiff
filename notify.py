import pystray
from PIL import Image, ImageDraw
from playlist_history import Diff
import http.server
import webbrowser


def _show_payload(payload):
    html = f"<!DOCTYPE html><html><head><title>{type(payload)}</title></head><body>"
    if isinstance(payload, Diff):
        for old, new in payload:
            if old is None:
                html += f'<p style="background-color:LightGreen">Added {new}</p>'
            elif new is None:
                html += f'<p style="background-color:IndianRed">Removed {old}</p>'
            else:
                html += f'<p style="background-color:Gold">Updated {old} -> {new}</p>'
    else:
        html += f"<p>{payload}<\p>"

    html += "</body></html>"

    class ReqHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=UTF-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            self.close_connection = True

    server = http.server.HTTPServer(('127.0.0.1', 0), ReqHandler)
    webbrowser.open_new(f"http://localhost:{server.server_address[1]}")
    server.handle_request()
    server.server_close()


def _make_icon():
    width = 64
    height = 64
    color1 = "blue"
    color2 = "red"

    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
    dc.rectangle((0, height // 2, width // 2, height), fill=color2)

    return image


def notify(msg: str, payload=None):
    interactive(msg)
    if payload is not None:
        _show_payload(payload)


def interactive(msg: str):

    icon = pystray.Icon("ytpldiff",
                        icon=_make_icon(),
                        title="ytpldiff",
                        menu=pystray.Menu(
                            pystray.MenuItem("continue",
                                             lambda icon, _: icon.stop(),
                                             default=True)))

    def setup(icon):
        icon.visible = True
        icon.notify(msg)

    icon.run(setup=setup)
