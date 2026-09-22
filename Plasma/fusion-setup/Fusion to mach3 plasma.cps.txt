/**
  Copyright (C) 2012-2021 by Autodesk, Inc.
  All rights reserved.

  Mach3 Plasma post processor configuration.

  $Revision: 43759 a148639d401c1626f2873b948fb6d996d3bc60aa $
  $Date: 2022-04-12 21:31:49 $

  FORKID {C59C057C-1427-4281-AE93-4F04BBA3F45E}
*/

description = "Mach3 Plasma";
vendor = "Artsoft";
vendorUrl = "http://www.machsupport.com";
legal = "Copyright (C) 2012-2021 by Autodesk, Inc.";
certificationLevel = 2;
minimumRevision = 45702;
highFeedrate = (unit == IN) ? 100 : 2500;

longDescription = "Generic post for Mach3 plasma.";

extension = "tap";
setCodePage("ascii");

capabilities = CAPABILITY_JET;
tolerance = spatial(0.002, MM);

minimumChordLength = spatial(0.25, MM);
minimumCircularRadius = spatial(0.01, MM);
maximumCircularRadius = spatial(1000, MM);
minimumCircularSweep = toRad(0.01);
maximumCircularSweep = toRad(180);
allowHelicalMoves = false;
allowedCircularPlanes = 1 << PLANE_XY; // only XY

// user-defined properties
properties = {
  writeMachine: {
    title      : "Write machine",
    description: "Output the machine settings in the header of the code.",
    group      : "formats",
    type       : "boolean",
    value      : true,
    scope      : "post"
  },
  showSequenceNumbers: {
    title      : "Use sequence numbers",
    description: "Use sequence numbers for each block of outputted code.",
    group      : "formats",
    type       : "boolean",
    value      : true,
    scope      : "post"
  },
  sequenceNumberStart: {
    title      : "Start sequence number",
    description: "The number at which to start the sequence numbers.",
    group      : "formats",
    type       : "integer",
    value      : 10,
    scope      : "post"
  },
  sequenceNumberIncrement: {
    title      : "Sequence number increment",
    description: "The amount by which the sequence number is incremented by in each block.",
    group      : "formats",
    type       : "integer",
    value      : 5,
    scope      : "post"
  },
  separateWordsWithSpace: {
    title      : "Separate words with space",
    description: "Adds spaces between words if 'yes' is selected.",
    group      : "formats",
    type       : "boolean",
    value      : true,
    scope      : "post"
  },
  pierceDelay: {
    title      : "Pierce delay",
    description: "Specifies the delay to pierce in seconds.",
    group      : "preferences",
    type       : "number",
    value      : 1,
    scope      : "post"
  },
  probeOffset: {
    title      : "Probe offset",
    description: "Specifies the offset for G31 probing.",
    group      : "probing",
    type       : "number",
    value      : 0,
    scope      : "post"
  },
  probe: {
    title      : "Probe",
    description: "Specifies whether to use probing.",
    group      : "probing",
    type       : "boolean",
    value      : false,
    scope      : "post"
  },
  useZAxis: {
    title      : "Use Z axis",
    description: "Specifies to enable the output for Z coordinates.",
    group      : "configuration",
    type       : "boolean",
    value      : false,
    scope      : "post"
  },
  pierceHeight: {
    title      : "Pierce Height",
    description: "Specifies the pierce height.",
    group      : "preferences",
    type       : "number",
    value      : 0,
    scope      : "post"
  },
  useG0: {
    title      : "Use G0",
    description: "Toggle between using G0 or G1 with a highFeedrate for rapid movements.",
    group      : "preferences",
    type       : "boolean",
    value      : true,
    scope      : "post"
  }
};

var gFormat = createFormat({prefix:"G", decimals:0});
var mFormat = createFormat({prefix:"M", decimals:0});

var xyzFormat = createFormat({decimals:(unit == MM ? 3 : 4), forceDecimal:true});
var zFormat = createFormat({decimals:(unit == MM ? 3 : 4), forceDecimal:true});
var abcFormat = createFormat({decimals:3, forceDecimal:true, scale:DEG});
var secFormat = createFormat({decimals:3, forceDecimal:true}); // seconds - range 0.001-1000
var feedFormat = createFormat({decimals:(unit == MM ? 2 : 3), forceDecimal:true});

var xOutput = createVariable({prefix:"X"}, xyzFormat);
var yOutput = createVariable({prefix:"Y"}, xyzFormat);
var zOutput = createVariable({prefix:"Z"}, zFormat);
var aOutput = createVariable({prefix:"A"}, abcFormat);
var bOutput = createVariable({prefix:"B"}, abcFormat);
var cOutput = createVariable({prefix:"C"}, abcFormat);
var feedOutput = createVariable({prefix:"F"}, feedFormat);

// circular output
var iOutput = createReferenceVariable({prefix:"I", force:true}, xyzFormat);
var jOutput = createReferenceVariable({prefix:"J", force:true}, xyzFormat);
var kOutput = createReferenceVariable({prefix:"K", force:true}, xyzFormat);

var gMotionModal = createModal({force:true}, gFormat); // modal group 1 // G0-G3, ...
var gAbsIncModal = createModal({}, gFormat); // modal group 3 // G90-91
var gUnitModal = createModal({}, gFormat); // modal group 6 // G20-22

// collected state
var sequenceNumber;
var initialG31 = false;

/**
  Writes the specified block.
*/
function writeBlock() {
  if (getProperty("showSequenceNumbers")) {
    writeWords2("N" + sequenceNumber, arguments);
    sequenceNumber += getProperty("sequenceNumberIncrement");
  } else {
    writeWords(arguments);
  }
}

function formatComment(text) {
  return "(" + String(text).replace(/[()]/g, "") + ")";
}

/**
  Output a comment.
*/
function writeComment(text) {
  writeln(formatComment(text));
}

function onOpen() {
  if (getProperty("useZAxis")) {
    zFormat.setOffset(getProperty("pierceHeight"));
    zOutput = createVariable({prefix:"Z"}, zFormat);
  } else {
    zOutput.disable();
  }

  if (!getProperty("separateWordsWithSpace")) {
    setWordSeparator("");
  }

  sequenceNumber = getProperty("sequenceNumberStart");

  /*
  if (programName) {
    writeComment(programName);
  }
*/
  if (programComment) {
    writeComment(programComment);
  }

  // dump machine configuration
  var vendor = machineConfiguration.getVendor();
  var model = machineConfiguration.getModel();
  var description = machineConfiguration.getDescription();

  if (getProperty("writeMachine") && (vendor || model || description)) {
    writeComment(localize("Machine"));
    if (vendor) {
      writeComment("  " + localize("vendor") + ": " + vendor);
    }
    if (model) {
      writeComment("  " + localize("model") + ": " + model);
    }
    if (description) {
      writeComment("  " + localize("description") + ": "  + description);
    }
  }

  // absolute coordinates and feed per min
  writeBlock(gAbsIncModal.format(90));

  switch (unit) {
  case IN:
    writeBlock(gUnitModal.format(70)); // or use M20
    break;
  case MM:
    writeBlock(gUnitModal.format(71)); // or use M21
    break;
  }

}

function onComment(message) {
  writeComment(message);
}

/** Force output of X, Y, and Z. */
function forceXYZ() {
  xOutput.reset();
  yOutput.reset();
  zOutput.reset();
}

/** Force output of A, B, and C. */
function forceABC() {
  aOutput.reset();
  bOutput.reset();
  cOutput.reset();
}

/** Force output of X, Y, Z, A, B, C, and F on next output. */
function forceAny() {
  forceXYZ();
  forceABC();
}

function onParameter(name, value) {
}

var currentWorkPlaneABC = undefined;

function forceWorkPlane() {
  currentWorkPlaneABC = undefined;
}

var closestABC = false; // choose closest machine angles
var currentMachineABC;

function getWorkPlaneMachineABC(workPlane) {
  var W = workPlane; // map to global frame

  var abc = machineConfiguration.getABC(W);
  if (closestABC) {
    if (currentMachineABC) {
      abc = machineConfiguration.remapToABC(abc, currentMachineABC);
    } else {
      abc = machineConfiguration.getPreferredABC(abc);
    }
  } else {
    abc = machineConfiguration.getPreferredABC(abc);
  }

  try {
    abc = machineConfiguration.remapABC(abc);
    currentMachineABC = abc;
  } catch (e) {
    error(
      localize("Machine angles not supported") + ":"
      + conditional(machineConfiguration.isMachineCoordinate(0), " A" + abcFormat.format(abc.x))
      + conditional(machineConfiguration.isMachineCoordinate(1), " B" + abcFormat.format(abc.y))
      + conditional(machineConfiguration.isMachineCoordinate(2), " C" + abcFormat.format(abc.z))
    );
  }

  var direction = machineConfiguration.getDirection(abc);
  if (!isSameDirection(direction, W.forward)) {
    error(localize("Orientation not supported."));
    return new Vector();
  }

  if (!machineConfiguration.isABCSupported(abc)) {
    error(
      localize("Work plane is not supported") + ":"
      + conditional(machineConfiguration.isMachineCoordinate(0), " A" + abcFormat.format(abc.x))
      + conditional(machineConfiguration.isMachineCoordinate(1), " B" + abcFormat.format(abc.y))
      + conditional(machineConfiguration.isMachineCoordinate(2), " C" + abcFormat.format(abc.z))
    );
  }

  var tcp = false;
  if (tcp) {
    setRotation(W); // TCP mode
  } else {
    var O = machineConfiguration.getOrientation(abc);
    var R = machineConfiguration.getRemainingOrientation(abc, W);
    setRotation(R);
  }

  return abc;
}

function onSection() {

  writeln("");

  if (hasParameter("operation-comment")) {
    var comment = getParameter("operation-comment");
    if (comment) {
      writeComment(comment);
    }
  }

  switch (tool.type) {
  case TOOL_PLASMA_CUTTER:
    break;
  default:
    error(localize("The CNC does not support the required tool/process. Only plasma cutting is supported."));
    return;
  }

  switch (currentSection.jetMode) {
  case JET_MODE_THROUGH:
    break;
  case JET_MODE_ETCHING:
    error(localize("Etch cutting mode is not supported."));
    break;
  case JET_MODE_VAPORIZE:
    error(localize("Vaporize cutting mode is not supported."));
    break;
  default:
    error(localize("Unsupported cutting mode."));
    return;
  }

  { // pure 3D
    var remaining = currentSection.workPlane;
    if (!isSameDirection(remaining.forward, new Vector(0, 0, 1))) {
      error(localize("Tool orientation is not supported."));
      return;
    }
    setRotation(remaining);
  }

  forceAny();

  var initialPosition = getFramePosition(currentSection.getInitialPosition());
  var zIsOutput = false;
  if (getProperty("useZAxis") && !getProperty("probe")) {
    var previousFinalPosition = isFirstSection() ? initialPosition : getFramePosition(getPreviousSection().getFinalPosition());
    if (xyzFormat.getResultingValue(previousFinalPosition.z) <= xyzFormat.getResultingValue(initialPosition.z)) {
      if (getProperty("useG0")) {
        writeBlock(gMotionModal.format(0), zOutput.format(initialPosition.z));
      } else {
        writeBlock(gMotionModal.format(1), zOutput.format(initialPosition.z), feedOutput.format(highFeedrate));
      }
      zIsOutput = true;
    }
  }

  if (getProperty("useG0")) {
    writeBlock(gMotionModal.format(0), xOutput.format(initialPosition.x), yOutput.format(initialPosition.y));
  } else {
    writeBlock(gMotionModal.format(1), xOutput.format(initialPosition.x), yOutput.format(initialPosition.y), feedOutput.format(highFeedrate));
  }
  initialG31 = true;
  writeG31();

  if (getProperty("useZAxis") && !zIsOutput) {
    if (getProperty("useG0")) {
      writeBlock(gMotionModal.format(0), zOutput.format(initialPosition.z));
    } else {
      writeBlock(gMotionModal.format(1), zOutput.format(initialPosition.z), feedOutput.format(highFeedrate));
    }
  }
}

function onDwell(seconds) {
  if (seconds > 99999.999) {
    warning(localize("Dwelling time is out of range."));
  }
  seconds = clamp(0.001, seconds, 99999.999);
  writeBlock(gFormat.format(4), "P" + secFormat.format(seconds));
}

function onCycle() {
}

function getCommonCycle(x, y, z, r) {
}

function onCyclePoint(x, y, z) {
}

function onCycleEnd() {
}

var pendingRadiusCompensation = -1;

function onRadiusCompensation() {
  pendingRadiusCompensation = radiusCompensation;
}

function writeG31() {
  if (getProperty("probe")) {
    var f = (hasParameter("operation:tool_feedEntry") ? getParameter("operation:tool_feedEntry") : toPreciseUnit(1000, MM));
    writeBlock(gFormat.format(31), "Z" + xyzFormat.format(-100), feedOutput.format(f));
    writeBlock(gFormat.format(92), "Z" + xyzFormat.format(getProperty("probeOffset")));
    feedOutput.reset();
    zOutput.reset();
  }
}

var powerIsOn = false;
function onPower(power) {
  initialG31 = false;
  writeBlock(mFormat.format(power ? 3 : 5));
  powerIsOn = power;
  if (power) {
    onDwell(getProperty("pierceDelay"));
    if (zFormat.isSignificant(getProperty("pierceHeight"))) {
      feedOutput.reset();
      var f = (hasParameter("operation:tool_feedEntry") ? getParameter("operation:tool_feedEntry") : toPreciseUnit(1000, MM));
      zFormat.setOffset(0);
      zOutput = createVariable({prefix:"Z"}, zFormat);
      writeBlock(gMotionModal.format(1), zOutput.format(getCurrentPosition().z), feedOutput.format(f));
    }
  } else {
    if (zFormat.isSignificant(getProperty("pierceHeight"))) {
      zFormat.setOffset(getProperty("pierceHeight"));
      zOutput = createVariable({prefix:"Z"}, zFormat);
    }
    writeln("");
  }
}

function onRapid(_x, _y, _z) {
  var x = xOutput.format(_x);
  var y = yOutput.format(_y);
  var z = zOutput.format(_z);
  // if plunge move, activate probe if enabled
  if (!x && !y && z && (_z < getCurrentPosition().z) && !initialG31 && !powerIsOn) {
    writeG31();
  }
  if (x || y || z) {
    if (pendingRadiusCompensation >= 0) {
      error(localize("Radius compensation mode cannot be changed at rapid traversal."));
      return;
    }
    if (getProperty("useG0")) {
      writeBlock(gMotionModal.format(0), x, y, z);
    } else {
      writeBlock(gMotionModal.format(1), x, y, z, feedOutput.format(highFeedrate));
    }
    feedOutput.reset();
  }
}

function onLinear(_x, _y, _z, feed) {
  // at least one axis is required
  if (pendingRadiusCompensation >= 0) {
    // ensure that we end at desired position when compensation is turned off
    xOutput.reset();
    yOutput.reset();
  }
  var x = xOutput.format(_x);
  var y = yOutput.format(_y);
  var z = zOutput.format(_z);
  var f = feedOutput.format(feed);
  // if plunge move, activate probe if enabled
  if (!x && !y && z && (_z < getCurrentPosition().z) && !initialG31 && !powerIsOn) {
    writeG31();
  }
  if (x || y || (z && !powerIsOn)) {
    if (pendingRadiusCompensation >= 0) {
      pendingRadiusCompensation = -1;
      switch (radiusCompensation) {
      case RADIUS_COMPENSATION_LEFT:
        writeBlock(gMotionModal.format(1), gFormat.format(41), x, y, z, f);
        break;
      case RADIUS_COMPENSATION_RIGHT:
        writeBlock(gMotionModal.format(1), gFormat.format(42), x, y, z, f);
        break;
      default:
        writeBlock(gMotionModal.format(1), gFormat.format(40), x, y, z, f);
      }
    } else {
      writeBlock(gMotionModal.format(1), x, y, z, f);
    }
  }
}

function onRapid5D(_x, _y, _z, _a, _b, _c) {
  error(localize("The CNC does not support 5-axis simultaneous toolpath."));
}

function onLinear5D(_x, _y, _z, _a, _b, _c, feed) {
  error(localize("The CNC does not support 5-axis simultaneous toolpath."));
}

function onCircular(clockwise, cx, cy, cz, x, y, z, feed) {
  if (pendingRadiusCompensation >= 0) {
    error(localize("Radius compensation cannot be activated/deactivated for a circular move."));
    return;
  }

  var start = getCurrentPosition();

  if (isFullCircle()) {
    if (isHelical()) {
      linearize(tolerance);
      return;
    }
    switch (getCircularPlane()) {
    case PLANE_XY:
      writeBlock(gMotionModal.format(clockwise ? 2 : 3), xOutput.format(x), iOutput.format(cx - start.x, 0), jOutput.format(cy - start.y, 0), feedOutput.format(feed));
      break;
    default:
      linearize(tolerance);
    }
  } else {
    switch (getCircularPlane()) {
    case PLANE_XY:
      writeBlock(gMotionModal.format(clockwise ? 2 : 3), xOutput.format(x), yOutput.format(y), iOutput.format(cx - start.x, 0), jOutput.format(cy - start.y, 0), feedOutput.format(feed));
      break;
    default:
      linearize(tolerance);
    }
  }
}

var mapCommand = {
  COMMAND_STOP         : 0,
  COMMAND_OPTIONAL_STOP: 1
};

function onCommand(command) {
  switch (command) {
  case COMMAND_POWER_ON:
    return;
  case COMMAND_POWER_OFF:
    return;
  case COMMAND_LOCK_MULTI_AXIS:
    return;
  case COMMAND_UNLOCK_MULTI_AXIS:
    return;
  case COMMAND_BREAK_CONTROL:
    return;
  case COMMAND_TOOL_MEASURE:
    return;
  }

  var stringId = getCommandStringId(command);
  var mcode = mapCommand[stringId];
  if (mcode != undefined) {
    writeBlock(mFormat.format(mcode));
  } else {
    onUnsupportedCommand(command);
  }
}

function onSectionEnd() {
  forceAny();
}

function onClose() {
  writeBlock(mFormat.format(30));
}

function setProperty(property, value) {
  properties[property].current = value;
}
