import ivport
import os
# raspistill capture
def capture(camera):
    "Se ejecutara la aplicacion raspistill de raspberry"
    cmd = "raspistill -t 10 -o still_CAM%d.jpg" % camera
    ret = os.system(cmd)
    print "cam %d returned %s" % (camera,ret)


iv = ivport.IVPort(ivport.TYPE_QUAD2,iv_jumper='A')
#iv.camera_open(camera_v2=True, resolution=(640, 480))

iv.camera_change(1)
capture(1)
iv.camera_change(2)
capture(2)
iv.camera_change(3)
capture(3)
iv.camera_change(4)
capture(4)
iv.close()


