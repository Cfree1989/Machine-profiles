+================================================
+                                                
+ ez-Router/Mach3/VA3D - Vectric machine output configuration file   
+                                                
+================================================
+                                                
+ History                                        
+                                                
+ Who    When       What                         
+ ======== ========== ===========================
+ JohnJ.     06/06/2006 Written  
+ JohnJ.     04/04/07 revised-spindle speed
+                     added Arc moves 
+ JohnJ.     05/13/07 Corrected I and J commands
+ John J.    03/11/08 Removed Arcs               
+================================================

POST_NAME = "ez-Router Mach3 (VA3D) (*.tap)"

FILE_EXTENSION = "tap"

UNITS = "INCHES"

+------------------------------------------------
+    Line terminating characters                 
+------------------------------------------------

LINE_ENDING = "[13][10]"

+------------------------------------------------
+    Block numbering                             
+------------------------------------------------

LINE_NUMBER_START     = 0
LINE_NUMBER_INCREMENT = 10
LINE_NUMBER_MAXIMUM = 999999

+================================================
+                                                
+    Formating for variables                     
+                                                
+================================================

VAR LINE_NUMBER = [N|A|N|1.0]
VAR SPINDLE_SPEED = [S|A|S|1.0]
VAR FEED_RATE = [F|C|F|1.1]
VAR X_POSITION = [X|C|X|1.4]
VAR Y_POSITION = [Y|C|Y|1.4]
VAR Z_POSITION = [Z|C|Z|1.4]
VAR X_HOME_POSITION = [XH|A|X|1.4]
VAR Y_HOME_POSITION = [YH|A|Y|1.4]
VAR Z_HOME_POSITION = [ZH|A|Z|1.4]

+================================================
+                                                
+    Block definitions for toolpath output       
+                                                
+================================================

+---------------------------------------------------
+  Commands output at the start of the file
+---------------------------------------------------

begin HEADER
"( [TP_FILENAME] )"
"[N]G90G80G49"
"[N]m05"
"[N]M06 T[T]"
"[N][S]"
"[N]M03"
"[N]G00[ZH]"
"[N]G00[XH][YH]"

+---------------------------------------------------
+  Commands output for rapid moves 
+---------------------------------------------------

begin RAPID_MOVE

"[N]G00[X][Y][Z]"


+---------------------------------------------------
+  Commands output for the first feed rate move
+---------------------------------------------------

begin FIRST_FEED_MOVE

"[N]G01[X][Y][Z][F]"


+---------------------------------------------------
+  Commands output for feed rate moves
+---------------------------------------------------

begin FEED_MOVE

"[N][X][Y][Z]"



+---------------------------------------------------
+  Commands output at toolchange
+---------------------------------------------------

begin TOOLCHANGE

"[N]M05"
"[N]G00 Z0.25"
"[N]M06 T[T]"
"[N][S]"
"[N]M03"

+---------------------------------------------------
+  Commands output at the end of the file
+---------------------------------------------------

begin FOOTER

"[N]G00[ZH]"
"[N]G00[XH][YH]"
"[N]M05M30"

