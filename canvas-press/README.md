# Sookie's Canvas Press

Published version: https://claude.ai/artifact/4SmmxXf5kBFZEC8BpBSXF1

A browser tool for printing needlepoint designs straight onto blank canvas. It replaces the CanvasTrue workflow with one where every scan stands on its own and everything can be edited.

## How it works

1. **Design**: add artwork (PNG, JPG, PSD or PDF). Each file becomes a layer, and you can set each layer's opacity, size and position before the layers are flattened into one picture. Pick the mesh (10, 12, 13, 14 or 18) and size in stitches, choose how many colors, and convert. Then edit stitch by stitch: paint, fill, pick color, erase, change any color, merge colors, undo and redo. **Read a painted canvas** takes a photo, scan or shop picture of a canvas that's already painted. It measures the mesh, finds every intersection, takes the painted color at each one, and turns bare canvas into unprinted stitches. It also cleans up the blurred in-between colors a photo leaves where two colors meet. That gives you an editable design you can print on a new canvas. The **Original** view shows the picture you read, with the stitch frame on it. The **Original picture on top** slider fades it over your stitches so you can compare. Designs show as **Canvas mesh** (threads and holes, like a real canvas) or **Squares**. **Move stitches** shifts the whole design, and the original moves with it. **Open stitch file** loads an image with one pixel per stitch, or an OXS chart, with no color changes. You can save a stitch image (PNG) or a printable chart (PNG).
2. **Scan**: print the Carrier sheet once. By default it has only four corner dots and thin corner marks, so it uses almost no ink. For the scan, put black paper behind the canvas or scan with the lid open so the holes look dark. A solid black window is optional. Tape the canvas inside the corner marks and scan the whole page at 300 or 600 dpi. The app finds the four dots and then every thread intersection, all from that one scan. There is no calibration sheet and no earlier scan it depends on. If the scan is upside down, it gets turned around. Teal points were found clearly, amber points were faint, and red points were guessed from their neighbors. Drag any point to fix it, or use arrow keys. **Next to check** steps through the doubtful points inside the design area. **Snapshot** shows the scan exactly as it came in, and you can save it.
3. **Print**: move the design on the canvas, boost the colors for canvas (richness, deepen, contrast, ink reach), and save a letter-size PDF at 300 or 600 dpi. Print it at 100% / Actual Size on the Carrier. **Preview** shows the design ink over your real threads. The printer nudge (in 1/200 inch steps) and a plain-paper test page are there if a printer lands off.

Everything runs in your browser. Nothing is uploaded, and there are no credits.

## How the alignment works

The four Carrier dots are printed by your own printer, so their spots in the scan link scan pixels to the printer's page. Each intersection the app finds is mapped through those dots onto the page. Each stitch is then drawn as a filled patch that runs out to the centers of the four holes around its intersection. Because the dots come from the same scan as the canvas, nothing carries over from an earlier scan.

## Opening it

Open `index.html` in Chrome, Edge or Safari, or use the published version.

Reading a PDF uses pdf.js from cdnjs. If that can't load, the app pulls the scanned image out of the PDF itself. That works for most scanner PDFs.
