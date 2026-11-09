import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui

Panel {
  id: root
  moduleName: "sonnt.t2"
  ipcTarget: "sonnt.t2"
  manageIpc: true
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  property var telemetry: ({})
  property int cpuTemp: telemetry.cpu_temp_c || 0
  property int gpuTemp: telemetry.gpu_temp_c || 0
  property string gpuStatus: telemetry.gpu_runtime_status || "unknown"
  property real systemWatts: telemetry.system_watts || 0
  property int chargeLimit: telemetry.charge_limit || 100
  property string batStatus: telemetry.battery_status || "Discharging"
  property int batCapacity: telemetry.battery_capacity || 0
  property int fan1Rpm: (telemetry.fans_rpm && telemetry.fans_rpm.fan1_input) || 0
  property int fan2Rpm: (telemetry.fans_rpm && telemetry.fans_rpm.fan2_input) || 0
  property bool cursorActive: false
  property int selectedIndex: 0

  function refresh() {
    if (!statusProc.running) statusProc.running = true
  }

  function runAction(command) {
    actionProc.command = command
    actionProc.running = true
  }

  function activateControl(index) {
    if (index < 3) {
      runAction(["pkexec", "/usr/libexec/t2-control", "set-fan-preset", ["quiet", "balanced", "auto"][index]])
    } else if (index < 5) {
      runAction(["pkexec", "/usr/libexec/t2-control", "set-charge-limit", index === 3 ? "80" : "100"])
    } else {
      runAction(["t2center"])
      root.close()
    }
  }

  onOpenedChanged: {
    if (opened) {
      cursorActive = false
      selectedIndex = 0
      refresh()
    }
  }

  Process {
    id: statusProc
    command: ["/usr/libexec/t2-control", "status"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          root.telemetry = JSON.parse(text)
        } catch (e) {}
      }
    }
  }

  Process {
    id: actionProc
    onExited: root.refresh()
  }

  Timer {
    interval: 3000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refresh()
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: ""
    tooltipText: "Apple T2 Mac\nCPU: " + root.cpuTemp + " °C | GPU: " + (root.gpuStatus === "suspended" ? "D3cold" : root.gpuStatus) + "\nFans: " + root.fan1Rpm + " / " + root.fan2Rpm + " RPM\nPower: " + Commons.I18n.formatNumber(root.systemWatts, 1) + " W"
    onPressed: function(b) {
      if (b === Qt.RightButton) root.runAction(["t2center"])
      else if (b === Qt.LeftButton) root.toggle()
    }
  }

  KeyboardPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: panel.loadedContent
    contentWidth: panel.fittedContentWidth(Style.space(380))
    contentHeight: panel.fittedContentHeight(panel.loadedContentHeight)

    content: PanelKeyCatcher {
      anchors.fill: parent
      implicitHeight: column.implicitHeight
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }
      onMoveRequested: function(dx, dy) {
        if (!root.cursorActive) {
          root.cursorActive = true
          return
        }
        root.selectedIndex = Math.max(0, Math.min(5, root.selectedIndex + (dy || dx)))
      }
      onActivateRequested: if (root.cursorActive) root.activateControl(root.selectedIndex)

      Column {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: Style.space(14)

        PanelHero {
          title: "Apple T2"
          meta: "MacBookPro16,1"
          detail: root.systemWatts > 0 ? Commons.I18n.formatNumber(root.systemWatts, 1) + " W" : ""
          foreground: root.bar.foreground
          fontFamily: root.bar.fontFamily
          iconComponent: Text {
            textFormat: Text.PlainText
            text: ""
            color: root.bar.foreground
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.display
          }
        }

        PanelSeparator { foreground: root.bar.foreground }

        Column {
          width: parent.width
          spacing: Style.spacing.labelGap
          SectionHeader { text: "Graphics" }
          InfoPair { label: "Intel UHD 630"; value: "Primary" }
          InfoPair { label: "AMD Radeon 5300M"; value: root.gpuStatus === "suspended" ? "D3cold" : root.gpuStatus }
        }

        PanelSeparator { foreground: root.bar.foreground }

        Column {
          width: parent.width
          spacing: Style.space(10)
          SectionHeader { text: "Thermals & fans" }
          InfoPair { label: "CPU / GPU"; value: root.cpuTemp + " / " + root.gpuTemp + " °C" }
          InfoPair { label: "Left / right fan"; value: root.fan1Rpm + " / " + root.fan2Rpm + " RPM" }

          Row {
            id: fanRow
            width: parent.width
            spacing: Style.space(6)
            Repeater {
              model: ["Quiet", "Balanced", "SMC Auto"]
              ControlButton {
                required property string modelData
                required property int index
                controlIndex: index
                width: (fanRow.width - fanRow.spacing * 2) / 3
                text: modelData
              }
            }
          }
        }

        PanelSeparator { foreground: root.bar.foreground }

        Column {
          width: parent.width
          spacing: Style.space(10)
          SectionHeader { text: "Battery charge limit" }
          InfoPair { label: root.batStatus; value: root.batCapacity + "%" }

          Row {
            id: batteryRow
            width: parent.width
            spacing: Style.space(6)
            ControlButton {
              controlIndex: 3
              width: (batteryRow.width - batteryRow.spacing) / 2
              text: "80% limit"
              active: root.chargeLimit === 80
            }
            ControlButton {
              controlIndex: 4
              width: (batteryRow.width - batteryRow.spacing) / 2
              text: "100% full"
              active: root.chargeLimit === 100
            }
          }
        }

        PanelSeparator { foreground: root.bar.foreground }

        ControlButton {
          controlIndex: 5
          width: parent.width
          text: "Open T2 Center"
        }
      }
    }
  }

  component SectionHeader: PanelSectionHeader {
    foreground: root.bar.foreground
    fontFamily: root.bar.fontFamily
  }

  component InfoPair: RowLayout {
    property string label: ""
    property string value: ""
    width: parent.width
    spacing: Style.space(8)

    Text {
      textFormat: Text.PlainText
      text: parent.label
      color: root.bar.foreground
      opacity: 0.6
      font.family: root.bar.fontFamily
      font.pixelSize: Style.font.bodySmall
      Layout.fillWidth: true
      elide: Text.ElideRight
    }
    Text {
      textFormat: Text.PlainText
      text: parent.value
      color: root.bar.foreground
      font.family: root.bar.fontFamily
      font.pixelSize: Style.font.bodySmall
    }
  }

  component ControlButton: Button {
    required property int controlIndex
    foreground: root.bar.foreground
    fontFamily: root.bar.fontFamily
    fontSize: Style.font.bodySmall
    horizontalPadding: Style.spacing.controlPaddingX
    verticalPadding: Style.spacing.controlPaddingY + Style.space(2)
    bordered: true
    hasCursor: root.cursorActive && root.selectedIndex === controlIndex
    onClicked: root.activateControl(controlIndex)
    onHovered: function(hovered) {
      if (hovered) {
        root.cursorActive = true
        root.selectedIndex = controlIndex
      }
    }
  }
}
