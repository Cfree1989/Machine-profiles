+================================================
+
+ ez-Router - Vectric machine output configuration file
+
+================================================
+
+ History
+
+ Who When What
+ ======== ========== ===========================
+ John J. 9-26-08 Written
+ John J. 10-20-2009 Modified tool change Z height 
+ John J. Chnaged header format
+ John J. Added tool information text at tool change
+
+================================================
POST_NAME = "ez-Router-ATC"
FILE_EXTENSION = "tap"
UNITS = "inches"
+------------------------------------------------
+ Line terminating characters
+------------------------------------------------
LINE_ENDING = "[13][10]"
+------------------------------------------------
+ Block numbering
+------------------------------------------------
LINE_NUMBER_START = 0
LINE_NUMBER_INCREMENT = 10
LINE_NUMBER_MAXIMUM = 999999
+================================================
+
+ Formating for variables
+
+================================================
VAR LINE_NUMBER = [N|A|N|1.0]
VAR SPINDLE_SPEED = [S|A|S|1.0]
VAR FEED_RATE = [F|C|F|1.1]
VAR X_POSITION = [X|A|X|1.4]
VAR Y_POSITION = [Y|A|Y|1.4]
VAR Z_POSITION = [Z|C|Z|1.4]
VAR ARC_CENTRE_I_INC_POSITION = [I|A|I|1.4]
VAR ARC_CENTRE_J_INC_POSITION = [J|A|J|1.4]
VAR X_HOME_POSITION = [XH|A|X|1.4]
VAR Y_HOME_POSITION = [YH|A|Y|1.4]
VAR Z_HOME_POSITION = [ZH|A|Z|1.4]
+================================================
+
+ Block definitions for toolpath output
+
+================================================
+---------------------------------------------------
+ Commands output at the start of the file
+---------------------------------------------------
begin HEADER
""
"( ez-Router ATC )"
"( [TP_FILENAME])"
""
"[N] G80 G40 G90"
""
"[N] M06 T[T]"
"[N] G43 H[T]"
"[N] G00 [ZH]"
"[N] [S] "
"[N] M03"
"[N] [XH] [YH] [ZH] [F]"
+---------------------------------------------------
+ Commands output for rapid moves
+---------------------------------------------------
begin RAPID_MOVE
"[N] G00 [X] [Y] [Z]"
+---------------------------------------------------
+ Commands output for the first feed rate move
+---------------------------------------------------
begin FIRST_FEED_MOVE
"[N] G01 [X] [Y] [Z] [F]"
+---------------------------------------------------
+ Commands output for feed rate moves
+---------------------------------------------------
begin FEED_MOVE
"[N] [X] [Y] [Z]"
+---------------------------------------------------
+ Commands output for the first clockwise arc move
+---------------------------------------------------
begin FIRST_CW_ARC_MOVE
"[N] G02 [X] [Y] [I] [J] [F]"
+---------------------------------------------------
+ Commands output for clockwise arc move
+---------------------------------------------------
begin CW_ARC_MOVE
"[N] G02 [X] [Y] [I] [J]"
+---------------------------------------------------
+ Commands output for the first counterclockwise arc move
+---------------------------------------------------
begin FIRST_CCW_ARC_MOVE
"[N] G03 [X] [Y] [I] [J] [F]"
+---------------------------------------------------
+ Commands output for counterclockwise arc move
+---------------------------------------------------
begin CCW_ARC_MOVE
"[N] G03 [X] [Y] [I] [J]"
+---------------------------------------------------
+ Commands output at toolchange
+---------------------------------------------------
begin TOOLCHANGE
""
"[N] M6 T[T]"
"[N] G43 H[T]"
"[N] G00 [ZH]"
"[N] [S]"
"[N] M03"
+---------------------------------------------------
+ Commands output at the end of the file
+---------------------------------------------------
begin FOOTER
"[N] G00 [ZH]"
"[N] G00 [XH] [YH]"
"[N] M05"
"[N] M30"
