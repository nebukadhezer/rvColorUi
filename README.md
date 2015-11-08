# rvColorUi
a simple ui to rv's color node

a pyside dockable widget to expose rvColorNodes settings:
Gain,Gamma,Exposure, Offset, Saturation can be tweaked.
The settings can be copied to the clipboard and pasted in Nuke as a Grade Node.

Thanks to Mads Hagarth Lund for providing the nice color Wheels
Usage:
- drag is damped by .1 so the it is not tht responsive
- alt + drag is not damped
- middle mouse click resets value and color (beware to be over eiter value or the colors when u reset)

Known issues:
- get from nuke not working
- hue not setup yet
- hotkeys in RV are working (y-->rgb or e---> rgb) but are not directly updating the ui, frame change updates the ui
 graph-state-change event slows rv down even when only printing content from it


![image showcase](/docs/rvColorUi.jpg?raw=true "ColorUi")