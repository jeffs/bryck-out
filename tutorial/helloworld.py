#! /usr/bin/env python
"""Tutorial script to display "Hello world" with PySDL2."""

import os
import sys
import sdl2.ext

from distutils.sysconfig import get_python_lib

RESOURCES = sdl2.ext.Resources(
        os.path.join(get_python_lib(), 'sdl2', 'examples'),
        'resources')

# Create window.
sdl2.ext.init()

window = sdl2.ext.Window("Hello World!", size=(640, 480))
window.show()

factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
sprite = factory.from_image(RESOURCES.get_path("hello.bmp"))

spriterenderer = factory.create_sprite_render_system(window)

spriterenderer.render(sprite)
