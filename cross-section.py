import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    z = mo.ui.slider(1, 18, debounce=True, value=10)
    x = mo.ui.number(debounce=True, value=611)
    y = mo.ui.number(debounce=True, value=420)

    mo.md(f'''
    Zoom Level: {z}

    X: {x}, Y: {y}
    ''')
    return x, y, z


@app.cell
def _(x, y, z):
    X, Y, Z = x.value, y.value, z.value
    return X, Y, Z


@app.cell(hide_code=True)
def _(BytesIO, Image, mo, np, requests):
    _base_url = "https://tiles.mapterhorn.com/"
    def get_tile_url(x, y, z, base_url=_base_url):
        return base_url + f'{z}/{x}/{y}.webp'

    def get_image(url):
        resp = requests.get(url)
        return Image.open(BytesIO(resp.content))

    def get_tile(x, y, z):
        img = get_image(get_tile_url(x, y, z))
        img = np.array(img)
        img = img * [256, 1, 1/256]
        img = np.sum(img, axis=-1)
        img -= 128*256
        return img

    def show_tile(a):
        a = np.array(a)
        _min, _max = np.min(a), np.max(a)
        a -= _min
        a /= (_max - _min)
        a *= 256
        return mo.image(a)

    return get_image, get_tile


@app.cell
def _(mo):
    background_map = mo.ui.dropdown({'relief': 'relief', 'OpenTopoMap': 'https://tile.opentopomap.org/{}/{}/{}.png'}, value='relief')
    background_map
    return (background_map,)


@app.cell
def _(X, Y, Z, background_map, get_image, get_tile, plt):
    tile = get_tile(X, Y, Z)
    _shp = tile.shape
    _bg = tile if background_map.selected_key == 'relief' else get_image(background_map.value.format(Z, X, Y)).resize(_shp)

    def draw_with_line(ax: plt.Axes, widget):
        x, y = widget.x, widget.y
        ax.imshow(_bg)
        ax.axline((x[0], y[0]), (x[1], y[1]), color='red', ls='--')
        ax.plot(x, y, 'red')
        ax.set_xticks(())
        ax.set_yticks(())
        ax.invert_yaxis()

    return draw_with_line, tile


@app.cell
def _(ChartPuck, draw_with_line, mo, tile):
    _shp = tile.shape

    _puck = ChartPuck.from_callback(
        draw_fn=draw_with_line,
        x_bounds=[0, _shp[0]],
        y_bounds=[0, _shp[1]],
        x=[0, _shp[0]],
        y=[0, _shp[1]],
        # throttle=100,
        puck_radius=5,
        puck_color=['red', 'green']
    )

    puck = mo.ui.anywidget(_puck)
    return (puck,)


@app.cell
def _(map_coordinates, np, plt, puck, tile):
    _QUALITY = 200

    _p1, _p2 = (puck.x[0], puck.y[0]), (puck.x[1], puck.y[1])

    _coords = np.linspace(_p1, _p2, _QUALITY)
    _xs, _ys = _coords[:, 0], _coords[:, 1]

    _cross_section = map_coordinates(tile, [_ys, _xs])

    _fig, _ax = plt.subplots()
    _ax.plot(_cross_section, 'black')
    _ax.fill_between(
        np.arange(_QUALITY),
        _cross_section,
        np.ones(_QUALITY) * np.min(_cross_section) - 100,
        alpha=0.5, hatch='///', color='sandybrown'
    )
    _ax.scatter([0, _QUALITY-1], _cross_section[np.array([0, -1])], c=['red', 'green'])
    _ax.set_xticks(())
    plt.close(_fig)

    cross_section = _fig
    return (cross_section,)


@app.cell(hide_code=True)
def _(BytesIO, Image, cross_section, mo):
    def prepare_download():
        io = BytesIO()
        cross_section.savefig(io, format='png')
        return Image.open(io)

    dl = mo.download(prepare_download, 'section.png', mimetype='image/png')
    return (dl,)


@app.cell
def _(cross_section, dl, mo, puck):
    mo.hstack([puck, mo.vstack([cross_section, dl])], align='center')
    return


@app.cell
def _():
    import marimo as mo
    from wigglystuff import ChartPuck

    return ChartPuck, mo


@app.cell
def _():
    import numpy as np
    import requests
    from io import BytesIO
    from PIL import Image
    import matplotlib.pyplot as plt
    from scipy.ndimage import map_coordinates

    return BytesIO, Image, map_coordinates, np, plt, requests


if __name__ == "__main__":
    app.run()
