# rvColorUi
a simple ui to rv's color node

a pyside dockable widget to expose rvColorNodes settings:
Gain,Gamma,Exposure, Offset, Saturation can be tweaked.
The settings can be copied to the clipboard and pasted in Nuke as a Grade Node.

Known issues:
- get from nuke not working
- hue not setup yet
- hotkeys in RV are working (y-->rgb or e---> rgb) but are not directly updating the ui, frame change updates the ui
 graph-state-change event slows rv down even when only printing content from it
