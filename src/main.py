import sys, math, json
from pathlib import Path
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QDockWidget,
 QListWidget,QPushButton,QLabel,QDoubleSpinBox,QFormLayout,QSlider,QTabWidget,QFileDialog,
 QMessageBox,QComboBox,QSpinBox,QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *

class Viewport(QOpenGLWidget):
    def __init__(self, scene, selection):
        super().__init__(); self.scene=scene; self.selection=selection
        self.az=35; self.el=25; self.dist=14; self.pan=[0,0]; self.last=None
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST); glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA); glClearColor(.105,.12,.145,1)
    def resizeGL(self,w,h):
        glViewport(0,0,w,h); glMatrixMode(GL_PROJECTION); glLoadIdentity(); gluPerspective(45,w/max(1,h),.1,1000); glMatrixMode(GL_MODELVIEW)
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT); glLoadIdentity()
        ex=self.dist*math.cos(math.radians(self.el))*math.sin(math.radians(self.az)); ey=self.dist*math.sin(math.radians(self.el)); ez=self.dist*math.cos(math.radians(self.el))*math.cos(math.radians(self.az))
        gluLookAt(ex+self.pan[0],ey+self.pan[1],ez,self.pan[0],self.pan[1],0,0,1,0)
        self.grid()
        for i,o in enumerate(self.scene):
            glPushMatrix(); glTranslatef(*o["pos"]); glRotatef(o["rot"][0],1,0,0); glRotatef(o["rot"][1],0,1,0); glRotatef(o["rot"][2],0,0,1); glScalef(*o["scale"])
            glColor3f(*o.get("color",[.66,.72,.8])); self.mesh(o)
            if i==self.selection(): glColor3f(1,.56,.1); self.bounds(o)
            glPopMatrix()
        if self.selection() is not None: self.gizmo()
    def grid(self):
        glColor4f(.25,.29,.34,.7); glBegin(GL_LINES)
        for i in range(-20,21):
            glVertex3f(i,0,-20);glVertex3f(i,0,20);glVertex3f(-20,0,i);glVertex3f(20,0,i)
        glEnd()
        glBegin(GL_LINES); glColor3f(.85,.2,.2); glVertex3f(-5,0,0);glVertex3f(5,0,0);glColor3f(.2,.75,.25);glVertex3f(0,0,-5);glVertex3f(0,0,5);glColor3f(.25,.4,.95);glVertex3f(0,-5,0);glVertex3f(0,5,0);glEnd()
    def mesh(self,o):
        t=o["type"]
        if t=="Cube":
            v=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
            f=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)]
            glBegin(GL_QUADS)
            for face in f:
                for j in face:glVertex3fv(v[j])
            glEnd()
        elif t=="Sphere":
            q=gluNewQuadric(); gluSphere(q,1,o.get("segments",24),max(8,o.get("segments",24)//2))
        elif t=="Cylinder":
            q=gluNewQuadric(); gluCylinder(q,o.get("radius",1),o.get("radius",1),o.get("height",2),o.get("segments",24),4)
        elif t=="Cone":
            q=gluNewQuadric(); gluCylinder(q,o.get("radius",1),0,o.get("height",2),o.get("segments",24),4)
        elif t=="Plane":
            w=o.get("width",5); d=o.get("depth",5); glBegin(GL_QUADS);glVertex3f(-w,0,-d);glVertex3f(w,0,-d);glVertex3f(w,0,d);glVertex3f(-w,0,d);glEnd()
    def bounds(self,o):
        s=1; v=[(-s,-s,-s),(s,-s,-s),(s,s,-s),(-s,s,-s),(-s,-s,s),(s,-s,s),(s,s,s),(-s,s,s)]
        edges=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        glBegin(GL_LINES)
        for a,b in edges:glVertex3fv(v[a]);glVertex3fv(v[b])
        glEnd()
    def gizmo(self):
        # Screen-independent world-space axis marker at selected object's origin
        o=self.scene[self.selection()]; glPushMatrix();glTranslatef(*o["pos"]);glLineWidth(3);glBegin(GL_LINES)
        glColor3f(1,.2,.2);glVertex3f(0,0,0);glVertex3f(1.5,0,0)
        glColor3f(.2,1,.2);glVertex3f(0,0,0);glVertex3f(0,1.5,0)
        glColor3f(.2,.4,1);glVertex3f(0,0,0);glVertex3f(0,0,1.5);glEnd();glLineWidth(1);glPopMatrix()
    def mousePressEvent(self,e): self.last=e.position()
    def mouseMoveEvent(self,e):
        if self.last:
            d=e.position()-self.last
            if e.buttons()&Qt.MouseButton.LeftButton:self.az+=d.x()*.5;self.el=max(-89,min(89,self.el+d.y()*.5))
            elif e.buttons()&Qt.MouseButton.RightButton:self.pan[0]-=d.x()*.02;self.pan[1]+=d.y()*.02
            self.last=e.position();self.update()
    def wheelEvent(self,e):self.dist=max(2,min(100,self.dist-e.angleDelta().y()*.01));self.update()

class Main(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle("Motion Studio | Dev 0.3");self.resize(1320,820);self.scene=[];self.sel=None
        central=QWidget();lay=QVBoxLayout(central);lay.setContentsMargins(3,3,3,3)
        tools=QHBoxLayout()
        for typ in ["Cube","Sphere","Cylinder","Cone","Plane"]:
            b=QPushButton("＋ "+typ);b.clicked.connect(lambda _,t=typ:self.add(t));tools.addWidget(b)
        for label,fn in [("Clone",self.clone),("Delete",self.delete),("Save",self.save),("Open",self.open)]:
            b=QPushButton(label);b.clicked.connect(fn);tools.addWidget(b)
        tools.addStretch();lay.addLayout(tools)
        self.view=Viewport(self.scene,lambda:self.sel);lay.addWidget(self.view,1)
        tl=QHBoxLayout();tl.addWidget(QLabel("Timeline"));self.timeline=QSlider(Qt.Orientation.Horizontal);self.timeline.setRange(0,240);tl.addWidget(self.timeline,1);lay.addLayout(tl)
        self.setCentralWidget(central)
        dock=QDockWidget("Object Manager",self);self.objects=QListWidget();self.objects.currentRowChanged.connect(self.select);dock.setWidget(self.objects);self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,dock)
        dock2=QDockWidget("Attributes",self);tabs=QTabWidget()
        tr=QWidget();form=QFormLayout(tr);self.spin={}
        for group in ["Position","Rotation","Scale"]:
            for axis in "XYZ":
                sp=QDoubleSpinBox();sp.setRange(-99999,99999);sp.setDecimals(3);sp.setSingleStep(.1)
                sp.valueChanged.connect(lambda v,g=group,a=axis:self.set_transform(g,a,v));self.spin[group+axis]=sp;form.addRow(group+" "+axis,sp)
        tabs.addTab(tr,"Transform")
        prm=QWidget();pf=QFormLayout(prm);self.kind=QLabel("—");pf.addRow("Type",self.kind)
        self.radius=QDoubleSpinBox();self.radius.setRange(.01,100);self.radius.setValue(1);self.radius.valueChanged.connect(lambda v:self.set_param("radius",v));pf.addRow("Radius",self.radius)
        self.height=QDoubleSpinBox();self.height.setRange(.01,100);self.height.setValue(2);self.height.valueChanged.connect(lambda v:self.set_param("height",v));pf.addRow("Height",self.height)
        self.segs=QSpinBox();self.segs.setRange(3,128);self.segs.setValue(24);self.segs.valueChanged.connect(lambda v:self.set_param("segments",v));pf.addRow("Segments",self.segs)
        self.width=QDoubleSpinBox();self.width.setRange(.01,100);self.width.setValue(5);self.width.valueChanged.connect(lambda v:self.set_param("width",v));pf.addRow("Plane width",self.width)
        self.depth=QDoubleSpinBox();self.depth.setRange(.01,100);self.depth.setValue(5);self.depth.valueChanged.connect(lambda v:self.set_param("depth",v));pf.addRow("Plane depth",self.depth)
        tabs.addTab(prm,"Primitive")
        dock2.setWidget(tabs);self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,dock2)
        self.statusBar().showMessage("Orbit: left drag | Pan: right drag | Zoom: wheel | Object params in Attributes")
        self.add("Cube")
    def add(self,t):
        o={"name":f"{t} {len(self.scene)+1}","type":t,"pos":[0,0,0],"rot":[0,0,0],"scale":[1,1,1],"radius":1,"height":2,"segments":24,"width":5,"depth":5}
        self.scene.append(o);self.objects.addItem(o["name"]);self.objects.setCurrentRow(len(self.scene)-1);self.view.update()
    def select(self,row):
        self.sel=row if 0<=row<len(self.scene) else None
        if self.sel is not None:
            o=self.scene[row];self.kind.setText(o["type"])
            for group,key in [("Position","pos"),("Rotation","rot"),("Scale","scale")]:
                for i,a in enumerate("XYZ"):
                    sp=self.spin[group+a];sp.blockSignals(True);sp.setValue(o[key][i]);sp.blockSignals(False)
            for key,widget in [("radius",self.radius),("height",self.height),("segments",self.segs),("width",self.width),("depth",self.depth)]:
                widget.blockSignals(True);widget.setValue(o.get(key,widget.value()));widget.blockSignals(False)
        self.view.update()
    def set_transform(self,g,a,v):
        if self.sel is not None:self.scene[self.sel][{"Position":"pos","Rotation":"rot","Scale":"scale"}[g]]["XYZ".index(a)]=v;self.view.update()
    def set_param(self,k,v):
        if self.sel is not None:self.scene[self.sel][k]=v;self.view.update()
    def clone(self):
        if self.sel is None:return
        o=json.loads(json.dumps(self.scene[self.sel]));o["name"]+=" Copy";o["pos"][0]+=1
        self.scene.append(o);self.objects.addItem(o["name"]);self.objects.setCurrentRow(len(self.scene)-1);self.view.update()
    def delete(self):
        if self.sel is None:return
        i=self.sel;self.scene.pop(i);self.objects.takeItem(i);self.sel=None
        if self.scene:self.objects.setCurrentRow(min(i,len(self.scene)-1))
        self.view.update()
    def save(self):
        p,_=QFileDialog.getSaveFileName(self,"Save Scene","scene.motionstudio.json","Motion Studio (*.json)")
        if p:Path(p).write_text(json.dumps({"scene":self.scene,"frame":self.timeline.value()},indent=2),encoding="utf-8")
    def open(self):
        p,_=QFileDialog.getOpenFileName(self,"Open Scene","","Motion Studio (*.json)")
        if not p:return
        try:
            d=json.loads(Path(p).read_text(encoding="utf-8"));self.scene.clear();self.objects.clear()
            for o in d.get("scene",[]):self.scene.append(o);self.objects.addItem(o.get("name",o["type"]))
            self.timeline.setValue(d.get("frame",0));self.view.update()
            if self.scene:self.objects.setCurrentRow(0)
        except Exception as e:QMessageBox.critical(self,"Open error",str(e))
if __name__=="__main__":
    fmt=QSurfaceFormat();fmt.setDepthBufferSize(24);QSurfaceFormat.setDefaultFormat(fmt)
    app=QApplication(sys.argv);w=Main();w.show();sys.exit(app.exec())
