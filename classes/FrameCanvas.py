import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import ScanUtil as su
from classes import Scan

matplotlib.use('Qt5Agg')


class FrameCanvas(FigureCanvasQTAgg):

    def __init__(self, updateDisplay, showPointsBox, showIPVBox, dragButton):
        """Canvas for drawing frame and related point data."""
        # Related Scan object.
        self.linkedScan: Scan = None
        # Method to update display from calling class.
        self.updateDisplay = updateDisplay
        # Show Points Box and Show IPV Box on MainWindow.
        self.showPointsBox = showPointsBox
        self.showIPVBox = showIPVBox
        # Drag all points button on MainWindow.
        self.dragButton = dragButton
        # Enable click and drag of points.
        self.enableDrag = False
        # Check if drag was attempted.
        self.dragAttempted = False
        # Background (Frame with Scan details drawn) for blit.
        self.background = None
        # Coordinates of cursor when drag starts in ??? coordinates.
        self.xy = [0, 0]
        # Points that are dragged on canvas (pixels).
        self.framePointsPix = None

        # Figure to draw frames on.
        self.fig = Figure(dpi=100)
        self.fig.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        self.axis = self.fig.add_subplot(111)
        self.axis.patch.set_facecolor((0.5, 0.5, 0.5, 1))
        # Canvas functionality.
        self.canvas = self.fig.canvas
        self.canvas.mpl_connect('button_press_event', lambda x: self._axisPressEvent(x))
        self.canvas.mpl_connect('motion_notify_event', lambda x: self._axisMotionEvent(x))
        self.canvas.mpl_connect('button_release_event', lambda x: self._axisReleaseEvent(x))
        self.canvas.mpl_connect('scroll_event', lambda x: self._axisScrollEvent(x))

        super(FrameCanvas, self).__init__(self.fig)

    def _axisPressEvent(self, event):
        """Handle left presses on axis 1 and 2 (canvas displaying image)."""
        if self.linkedScan is not None:
            self.fd = self.linkedScan.frames[self.linkedScan.currentFrame - 1].shape
            self.dd = self.linkedScan.displayDimensions
            if self.dragButton.isChecked():
                self.xy = [event.xdata, event.ydata]
                self.enableDrag = True
                self.framePointsPix = self.linkedScan.getPointsOnFrame()

    def _axisMotionEvent(self, event):
        """Handle drag events on axis 1 and 2."""
        if self.linkedScan is not None:
            if self.enableDrag:
                self.dragAttempted = True
                xyNew = [event.xdata, event.ydata]
                dxy = [xyNew[0] - self.xy[0], xyNew[1] - self.xy[1]]
                self.linkedScan.clearFramePoints()
                # Drag each point on the frame by delta amount.
                for pointPix in self.framePointsPix:
                    # This y-portion of the equation is confusing, but it works.
                    pointDisplay = su.pixelsToDisplay([pointPix[0], self.fd[0] - pointPix[1]], self.fd, self.dd)
                    pointNew = [pointDisplay[0] + dxy[0], pointDisplay[1] - dxy[1]]
                    self.linkedScan.addOrRemovePoint(pointNew)
                self.updateDisplay()

    def _axisReleaseEvent(self, event):
        """Handle left releases on axis 1 and 2. AddRemove if no drag took place"""
        if self.linkedScan is not None:
            if not self.dragAttempted:
                if event.button == 1:
                    displayPoint = [event.x, event.y]
                    if self.showPointsBox.isChecked():
                        self.linkedScan.addOrRemovePoint(displayPoint)
                        self.updateDisplay()
        self.enableDrag = False
        self.dragAttempted = False

    def _axisScrollEvent(self, event):
        """Handle scroll events on axis (canvas displaying image)."""
        if self.linkedScan is not None:
            if event.button == 'up':
                self.linkedScan.navigate(Scan.NAVIGATION['w'])
            else:
                self.linkedScan.navigate(Scan.NAVIGATION['s'])
            self.updateDisplay()
            return

    def updateAxis(self):
        """Update axis with frame and points."""
        self.linkedScan.drawFrameOnAxis(self)

        # self.background = self.copy_from_bbox(self.axis.bbox)
        cfi = self.linkedScan.currentFrame - 1
        fd = self.linkedScan.frames[cfi].shape
        dd = self.linkedScan.displayDimensions
        # Draw points on canvas if box ticked.
        if self.showPointsBox.isChecked():
            su.drawPointDataOnAxis(self.axis, self.linkedScan.getPointsOnFrame(), fd, dd)
        # Draw IPV data on canvas if box ticked.
        if self.showIPVBox.isChecked():
            su.drawIPVDataOnAxis(self.axis, self.linkedScan.ipvData, self.linkedScan.frameNames[cfi], fd, dd)

        self.draw()
