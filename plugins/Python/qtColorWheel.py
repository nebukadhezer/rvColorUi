# big thanks to mads hagbarth lund for providing the code and of course to 
# https://code.google.com/p/dedafx-dev/source/browse/trunk/python/gui/qt/ColorWheel.py?r=3
# ben deda from whom this derived

import sys, math
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore

import datetime



class ColorWheelWidget(QtGui.QWidget):
    
    colorSignal = QtCore.Signal(list)
    
    def __init__(self, parent=None, mainDiameter=138, outerRingWidth=10,my_Knob=[1.0,1.0,1.0,1.0],name=''):
        QtGui.QWidget.__init__(self, parent)
        self.name = name
        # this is the pixel diameter of the actual color wheel, without the extra decorations drawn as part of this widget
        self.setMinimumSize(mainDiameter+22,mainDiameter+22)
        self.dim = mainDiameter
        self.offset = outerRingWidth
        self.ColorKnob = my_Knob
        self.colorWheelSensitivity = 0.1
        self.setstate = 0
        self.bMouseDown = False
        self.shiftDown = False
        self.ctrlDown = False
        self.altDown = False
        self.guiSelection = 0
        self.middleMouse = 0
        self.initialPoint = (0,0)    
        self.master_radius = (self.dim/2)+self.offset+1
        self.huepoint = (self.master_radius, self.master_radius)
        self.value_angle = 360
        self.value_angleSat = 0       
        color = QtGui.QColor(0,0,0,0).rgba()
        self.myTimer = QtCore.QTime()
 
        self.center = (self.master_radius, self.master_radius)
        # this is the color value that this widget represents
        self.color = QtGui.QColor()



        # the color wheel image, only needs to be generated once
        self.image = QtGui.QImage(self.master_radius*2, self.master_radius*2, QtGui.QImage.Format_ARGB32)
        # this is the image for the current color selection
        self.current_image = QtGui.QImage(self.master_radius*2, self.master_radius*2, QtGui.QImage.Format_ARGB32)
        self.current_image.fill(QtGui.QColor(self.color).rgba())
        self.current_imageB = QtGui.QImage(self.master_radius*2, self.master_radius*2, QtGui.QImage.Format_ARGB32)
        self.current_imageB.fill(QtGui.QColor(self.color).rgba())       
        # these are used for the current color selection image
        self.lastPoint = (self.master_radius, self.master_radius)
        self.currentPoint = (self.master_radius, self.master_radius)
        self.points = self.getRadialLinePoints((self.dim / 2), self.master_radius, 45)
        self.points2 = self.getRadialLinePoints((self.dim / 2), self.master_radius, 135)            
        self.image.fill(color)


        self.color.setRgbF(min(1,max(0,my_Knob[0])),min(1,max(0,my_Knob[1])),min(1,max(0,my_Knob[2])))


        self.luma = (my_Knob[3]/2.0)*255.0
        self.hue = self.color.hueF()*255.0
        self.sat = self.color.saturationF()*255.0
   

        self.setUIColor(self.hue,self.sat,self.luma) 

        for y in range(int(self.master_radius*2)):
            for x in range(int(self.master_radius*2)):
                d = 2 * self.getDist((x,y),self.center) / self.dim
                if d <= 1: #Hue Wheel
                    color = QtGui.QColor()
                    hue = self.getHue(x, y)
                    percent = max(0,min(1,(d - 0.90)*30))
                    color.setHsv(hue,(d*255),90+(165*percent),90+(165*percent)) #The dark part in the center

                    self.image.setPixel(x,y, color.rgba())
                else:
                    d2 = self.getDist((x,y),self.center) / (self.master_radius-1)
                    if d2 > 1: #MainBG                       
                        color = QtGui.QColor()
                        color.setAlpha(0)
                        self.image.setPixel(x,y, color.rgba())
                    else:
                        pass

        self.setUIColor(self.hue,self.sat,self.luma) 
        self.setColor(self.hue, self.sat, self.luma)


    def getRadialLinePoints(self, r_inner, r_outer, angle,distance=1.0):
        rad = math.radians(angle)
        sr = math.sin(rad)
        cr = math.cos(rad)
        x1 = r_outer - (r_outer * (sr*distance))
        y1 = r_outer - (r_outer * (cr*distance)) 
        x2 = r_outer - (r_inner * (sr*distance))
        y2 = r_outer - (r_inner * (cr*distance))
        return (x1, y1, x2, y2)
  
    def getRot(self, x, y):
        return ( math.degrees ( math.atan2 ( 2*(x - self.master_radius),2*(y - self.master_radius)))) % 360
    def getLum(self, x, y):
        return ( math.degrees ( math.atan2 ( 2.0*(x - self.master_radius),2.0*(y - self.master_radius)))) % 360

    def getHue(self, x, y):
        return ( math.degrees ( math.atan2 ( 2*(x - self.master_radius),2*(y - self.master_radius))) + 165 ) % 360
    
    def setColor(self, h, s, v):

        self.color.setHsvF(0.0,0.0,min(1,v/255.0))
        alpha = self.current_image.alphaChannel()
        self.current_image.fill(self.color.rgb())
        self.current_image.setAlphaChannel(alpha)
        self.color.setHsvF(min(1,h/255.0),1.0,min(1,v/255.0)) #Should be 255 and not 254.5 but it causes a unknown error!
        alpha = self.current_imageB.alphaChannel()
        self.current_imageB.fill(self.color.rgb())
        self.current_imageB.setAlphaChannel(alpha)
        self.update()      

    def setColorRgb(self,r,g,b):
        self.color.setRgb(r,g,b)
        alpha = self.current_image.alphaChannel()
        self.current_image.fill(self.color.rgb())
        self.current_image.setAlphaChannel(alpha)
        self.current_imageB.fill(self.color.rgb())
        self.current_imageB.setAlphaChannel(alpha)
        #self.colorSignal.emit(self.getRgbFloat())
        self.update()

    def reset(self,x):
        self.middleMouse = 1
        self.bMouseDown = True
        self.guiSelection = 0
        self.initialPoint = (self.center[0], self.center[1])
        self.lastPoint = (self.center[0], self.center[1]) 
        self.alterColor(self.lastPoint[0], self.lastPoint[1])
        self.guiSelection = 1
        self.initialPoint = (self.center[0], self.center[1])
        self.lastPoint = (self.center[0], self.center[1]) 
        self.alterColor(self.lastPoint[0], self.lastPoint[1]-10)
        self.lastPoint = self.currentPoint
        self.setColor(self.hue, self.sat, self.luma)
        self.setUIColor(self.hue,self.sat,self.luma)
        self.bMouseDown = False
        if not self.ColorKnob == "None":
            try:
                self.color.setHsvF(min(1,self.hue/255.0),min(1,self.sat/255.0),1.0)
                self.ColorKnob = [float(self.color.redF()),float(self.color.greenF()),float(self.color.blueF()),float(self.luma*2)/255]
                self.colorSignal.emit(self.getRgbFloat() )
            except: 
                print "Error trying to send values to color control. Make sure all layouts are set to 4 Colors and not 1"

        
    def getDist(self, (x1, y1), (x2, y2)):
        return math.sqrt((x2-x1)**2 + (y2-y1)**2)
    
    def getRgbFloat(self):
        #parent.GainEnabled?((parent.Gain.r-((parent.Gain.r+parent.Gain.g+parent.Gain.b)/3))*1)+(parent.Gain.a):1
        avg = (self.ColorKnob[0]+self.ColorKnob[1]+self.ColorKnob[2])/3.0
        ret = [(self.ColorKnob[0] - avg)*1+self.ColorKnob[3],
                (self.ColorKnob[1] - avg)*1+self.ColorKnob[3],
                (self.ColorKnob[2] - avg)*1+self.ColorKnob[3],
                self.name,
                True]
        return ret
    
        
    def paintEvent(self, evt):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen()
        if not self.ColorKnob == "None":
            try:
                if self.setstate > 0:
                    self.color.setHsvF(min(1,self.hue/255.0),min(1,self.sat/255.0),1.0)
                    self.ColorKnob = [float(self.color.redF()),float(self.color.greenF()),float(self.color.blueF()),float(self.luma*2)/255]
                    self.colorSignal.emit(self.getRgbFloat() )
                if self.setstate > 1:
                    self.setstate = 0

            except: 
                print "Error trying to send values to color control. Make sure all layouts are set to 4 Colors and not 1"
        self.color.setHsvF(min(1,self.hue/255.0),min(1,self.sat/255.0),min((self.luma/255.0)*2.0,1.0))
        brush = QtGui.QBrush(QtGui.QColor(self.color.rgb())) #Color of the elipse
        pen.setColor(QtGui.QColor(20,20,20)) #Outline Color
        pen.setWidth(2) #Outline Width
        painter.setPen(pen)
        
        painter.drawImage(0,0,self.image)
        #painter.drawImage(0,0,self.current_image)
        #painter.drawImage(0,0,self.current_imageB)
        r = self.dim/2 
        r2 = r + self.offset
        center = QtCore.QPoint(r2+2,r2+2) 
        center = QtCore.QPointF(self.center[0],self.center[1] )
        
        painter.drawEllipse(center, r, r ) #DRAW THE OUTER BLACK CIRCLE


   
        #LUMINANCE ARC
        pen.setWidth(3) #Outline Width
        pen.setColor(QtGui.QColor(150,150,150)) #Outline Color
        gradient = QtGui.QConicalGradient()
        gradient.setCenter(center)
        gradient.setAngle(-90)
        gradient.setColorAt(1, QtGui.QColor(255, 255, 255))
        gradient.setColorAt(0.497, QtGui.QColor(170, 170, 170))
        gradient.setColorAt(0.498, QtGui.QColor(255, 255, 255))
        gradient.setColorAt(0.5, QtGui.QColor(255, 255, 255))
        gradient.setColorAt(0.502, QtGui.QColor(255, 255, 255))
        gradient.setColorAt(0.503, QtGui.QColor(170, 170, 170))
        gradient.setColorAt(0, QtGui.QColor(70, 70, 70))
        pen.setBrush(gradient)

        painter.setPen(pen)    
        rectangle = QtCore.QRectF(self.center[0]-((self.dim*1.1)/2), self.center[1]-((self.dim*1.1)/2), self.dim*1.1, self.dim*1.1)     
        startAngle = -90*16

        spanAngle = (self.value_angle)*16
        painter.drawArc(rectangle, startAngle, spanAngle)


        pen.setWidth(1) #Outline Width
        pen.setColor(QtGui.QColor(20,20,20)) #Outline Color
        painter.setPen(pen)
        #painter.drawEllipse(center, r-8, r-8) #DRAW THE INNER BLACK CIRCLE

        pen.setColor(QtGui.QColor(200,200,200)) #Outline Color
        painter.setPen(pen)
        #Middle Crosshair
        painter.drawLine((self.master_radius)+4,(self.master_radius),(self.master_radius)-4,(self.master_radius))
        painter.drawLine((self.master_radius),(self.master_radius)+4,(self.master_radius),(self.master_radius)-4)

        pen.setWidth(6) #Outline Width
        painter.setPen(pen)
        (x1,y1,x2,y2) = self.points
        (x1,y1,x2,y2) = self.points2


        #Draw the GuideLines
        pen.setWidth(1.99)
        pen.setColor(QtGui.QColor(220,220,220))
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        painter.setPen(pen)
        (hpx, hpy) =  self.huepoint
        d = self.getDist((hpx,hpy),self.center)
        if self.bMouseDown == False: #Hide the guidelines when the mouse is not clicked
            pass
        else:
            (x1,y1,x2,y2) = self.getRadialLinePoints(0, self.master_radius, ((self.hue/255)*360)+15,0.80) 
            painter.drawLine(x1,y1,x2,y2)
            if d > 46: #If the radial is in the bright area, then display a dark version
                pen.setColor(QtGui.QColor(20,20,20))  
                painter.setPen(pen)
            if d != 0:
                painter.drawEllipse(QtCore.QPointF(self.master_radius, self.master_radius), d, d)


        #Draw Hue Dot
        pen.setWidth(1)
        pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        if self.luma > 90:
            pen.setColor(QtGui.QColor(0,0,0))
        else:
            pen.setColor(QtGui.QColor(220,220,220))
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawEllipse(QtCore.QPointF(hpx, hpy), 5, 5)



    def setUIColor(self,h,s,v):
        (x1,y1,x2,y2) = self.getRadialLinePoints((self.dim / 2.0), self.master_radius,  ((self.hue/255)*360)+15,(s/255.0))
        self.huepoint = (x2,y2)
        self.lastPoint = (x2,y2)
        self.currentPoint = (x2,y2)
        #Saturation
        self.value_angleSat = (1.0-((s/255.0) * 90.0)) + 135.0       

        #Luminance
        self.value_angle = ((v/255.0) * 360.0) 


        
    def alterColor(self, x, y):    
        d = 2.0 * self.getDist((x,y),self.center) / self.dim
        if self.guiSelection == 0:
            if self.getDist((x,y),self.center) >= (self.dim/2.0):
                Percent = self.getDist((x,y),self.center) / (self.dim/2.0)
                prex = (((x-self.center[0]) / Percent) * 1)+self.center[0]
                prey = (((y-self.center[1]) / Percent) * 1)+self.center[1]
                self.initialPoint = (self.initialPoint[0]-(prex-x), self.initialPoint[1]-(prey-y))
                x = prex
                y = prey
            hue = self.getHue(x, y)

            self.value_angleSat = (1.0-((self.getDist((x,y),self.center) / (self.dim/2.0)) * 90.0)) + 135.0  
            self.hue = (hue/360)*255
            self.sat = min(d*255.0,255.0)
            self.huepoint = (x,y)
            self.setColor(hue,min(d*255.0,255.0),self.luma)
        
        elif self.guiSelection == 1:
            self.value_angle = self.getRot(x, y)
            lum = self.getLum(x, y)
            v = (lum/360.0)*255.0
            self.setColor(self.color.hueF(), self.color.saturationF(), v)
            self.luma = v


        else:
            pass


    def mousePressEvent(self, evt):
        self.setstate = 1
        self.myTimer.start()
        
        d = 2 * self.getDist((evt.x(), evt.y()),self.center) / self.dim
        if evt.button() == QtCore.Qt.MouseButton.MiddleButton:
            self.middleMouse = 1
        else:
            self.middleMouse = 0
        if d <= 1: 
            self.guiSelection = 0
            if self.middleMouse == 1:
                self.initialPoint = (self.center[0], self.center[1])
                self.lastPoint = (self.center[0], self.center[1]) 
                self.alterColor(self.lastPoint[0], self.lastPoint[1])
            else:
                self.initialPoint = (evt.x(), evt.y())
                self.alterColor(self.lastPoint[0], self.lastPoint[1])
        else:
            d = self.getDist((evt.x(), evt.y()),self.center) / self.master_radius
            if d <= 1:
                self.guiSelection = 1
                if self.middleMouse == 1:
                    self.initialPoint = (self.center[0], self.center[1])
                    self.lastPoint = (self.center[0], self.center[1]) 
                    self.alterColor(self.lastPoint[0], self.lastPoint[1]-10)
                else:
                    self.alterColor(evt.x(), evt.y())
            else:
                self.guiSelection = 3
        self.bMouseDown = True




    def mouseMoveEvent(self, evt):
        self.setstate = 1
        nMilliseconds = self.myTimer.elapsed()
        if nMilliseconds < 1:
            pass
        else:

            modifiers = QtGui.QApplication.keyboardModifiers()
            self.shiftDown = False
            self.ctrlDown = False
            self.altDown = False
            self.colorWheelSensitivity = 0.1

            if modifiers == QtCore.Qt.ShiftModifier:
                self.shiftDown = True
            if modifiers == QtCore.Qt.ControlModifier:
                self.ctrlDown = True
            if modifiers == QtCore.Qt.AltModifier:
                self.altDown = True
                self.colorWheelSensitivity = 1
            if modifiers == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                self.ctrlDown = True
                self.shiftDown = True

            if self.bMouseDown and self.middleMouse == 0:
                if self.guiSelection == 1 or self.guiSelection == 2:
                    self.alterColor(evt.x(), evt.y())
                else:

                    x = (((evt.x()-self.initialPoint[0]) * self.colorWheelSensitivity))+self.lastPoint[0]
                    y = (((evt.y()-self.initialPoint[1]) * self.colorWheelSensitivity))+self.lastPoint[1]
                    self.alterColor(x, y)
                    self.currentPoint = (x, y) 
            self.myTimer.restart()
        

    def mouseReleaseEvent(self, evt):
        self.setstate = 2
        self.lastPoint = self.currentPoint
        self.setColor(self.hue, self.sat, self.luma)
        self.setUIColor(self.hue,self.sat,self.luma)
        self.bMouseDown = False
            
def main(args):
    app=QtGui.QApplication(args)
    win=ColorWheelWidget()
    win.show()
    app.connect(app, QtCore.SIGNAL("lastWindowClosed()")
                 , app
                 , QtCore.SLOT("quit()")
                 )
    app.exec_()
  
if __name__=="__main__":
    main(sys.argv)