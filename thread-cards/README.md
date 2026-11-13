# Thread cards (3D print)

Dainty bobbin-style thread cards with a scalloped bottom edge, for the beginner kit.

| File | Threads | Size (mm) |
|---|---|---|
| `stl/thread_card_2_threads.stl` | 2 | 46 × 88 × 1.6 |
| `stl/thread_card_3_threads.stl` | 3 | 46 × 111 × 1.6 |
| `stl/thread_card_4_threads.stl` | 4 | 46 × 134 × 1.6 |

Features: rounded top tab with a 5.5 mm carabiner hole, Sookie's Needlepoint logo raised 0.4 mm on a 1.2 mm card (40 mm wide), and thread-catch slits with a V lead-in on every divider to tuck the thread ends.

**Printing:** lay flat, no supports, 0.2 mm layers, 100% infill (thin part), PLA or PETG.

To change sizes (thickness, number of scallops, etc.) edit the constants at the top of
`make_thread_cards.py` and run `python3 make_thread_cards.py`.

**Two colours (pink logo):** load `stl/two_color/..._CARD.stl` and `..._LOGO.stl` together
in your slicer as one multi-part object and give the logo pink filament. Or, on a single-colour
printer, add a filament change at the 1.2 mm layer.
