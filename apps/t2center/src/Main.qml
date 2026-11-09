import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    id: win
    width: 880
    height: 600
    minimumWidth: 720
    minimumHeight: 500
    visible: true
    title: qsTr("Apple T2 Control Center")
    color: theme.background

    readonly property string uiFont: Qt.application.font.family
    readonly property string monoFont: "monospace"
    font.family: uiFont
    font.pixelSize: 13
    Material.theme: Material.Dark
    Material.accent: theme.accent
    Material.roundedScale: theme.radius

    property int activeTab: 0 // 0: Overview, 1: Fans, 2: Battery, 3: Transcode
    property bool helpVisible: false

    readonly property bool enteringPath: filePathInput.activeFocus
    Shortcut { sequence: "?"; context: Qt.ApplicationShortcut; enabled: !win.enteringPath; onActivated: win.helpVisible = !win.helpVisible }
    Shortcut { sequence: "Escape"; context: Qt.ApplicationShortcut; enabled: win.helpVisible; onActivated: win.helpVisible = false }
    Shortcut { sequence: "Q"; context: Qt.ApplicationShortcut; enabled: !win.enteringPath; onActivated: Qt.quit() }
    Shortcut { sequence: "R"; context: Qt.ApplicationShortcut; enabled: !win.enteringPath && !win.helpVisible; onActivated: backend.refresh() }
    Shortcut { sequence: "1"; context: Qt.ApplicationShortcut; enabled: !win.enteringPath && !win.helpVisible; onActivated: win.activeTab = 0 }
    Shortcut { sequence: "2"; context: Qt.ApplicationShortcut; enabled: !win.enteringPath && !win.helpVisible; onActivated: win.activeTab = 1 }
    Shortcut { sequence: "3"; context: Qt.ApplicationShortcut; enabled: !win.enteringPath && !win.helpVisible; onActivated: win.activeTab = 2 }
    Shortcut { sequence: "4"; context: Qt.ApplicationShortcut; enabled: !win.enteringPath && !win.helpVisible; onActivated: win.activeTab = 3 }

    // Keep Qt's keyboard, focus and accessibility behavior under the flat skin.
    component OmarchyButton: Button {
        id: btn
        property bool active: false
        property bool primary: false
        property int fontSize: 13
        implicitWidth: btnText.implicitWidth + 24
        implicitHeight: 32
        leftPadding: 12
        rightPadding: 12
        topPadding: 0
        bottomPadding: 0
        topInset: 0
        bottomInset: 0
        leftInset: 0
        rightInset: 0
        hoverEnabled: true
        focusPolicy: Qt.StrongFocus
        opacity: enabled ? 1 : 0.45
        background: Rectangle {
            radius: Math.min(4, theme.radius)
            color: btn.down ? theme.border
                 : btn.active || btn.primary ? theme.accent
                 : btn.hovered ? theme.border : theme.cardBackground
            border.color: btn.visualFocus ? theme.foreground : theme.border
            border.width: 1
        }
        contentItem: Text {
            id: btnText
            text: btn.text
            font.family: win.uiFont
            font.pixelSize: btn.fontSize
            color: btn.active || btn.primary ? theme.accentForeground : theme.foreground
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    // Main layout
    Item {
        anchors.fill: parent
        anchors.margins: 18
        focus: true
        // Buttons and text inputs consume Space before it bubbles here.
        Keys.onSpacePressed: event => {
            if (!win.helpVisible) backend.refresh()
            event.accepted = true
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 14

            // 1. Header Bar
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Text {
                    text: qsTr("T2 Center")
                    font.family: win.uiFont
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                    color: theme.foreground
                }

                Rectangle {
                    color: theme.cardBackground
                    radius: Math.min(4, theme.radius)
                    border.color: theme.border
                    border.width: 1
                    implicitWidth: modelText.implicitWidth + 16
                    implicitHeight: 24

                    Text {
                        id: modelText
                        anchors.centerIn: parent
                        text: "MacBookPro16,1"
                        font.family: win.monoFont
                        font.pixelSize: 11
                        color: theme.muted
                    }
                }

                Item { Layout.fillWidth: true }

                // Live Power Badge
                Rectangle {
                    color: theme.cardBackground
                    radius: Math.min(4, theme.radius)
                    border.color: backend.systemWatts > 35 ? theme.yellow : theme.green
                    border.width: 1
                    implicitWidth: wattsText.implicitWidth + 36
                    implicitHeight: 26

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6
                        Rectangle {
                            width: 6; height: 6; radius: 3
                            color: backend.systemWatts > 35 ? theme.yellow : theme.green
                        }
                        Text {
                            id: wattsText
                            text: backend.systemWatts > 0 ? (backend.systemWatts.toFixed(1) + " W") : "T2 Active"
                            font.family: win.monoFont
                            font.pixelSize: 12
                            font.bold: true
                            color: theme.foreground
                        }
                    }
                }

                OmarchyButton {
                    text: qsTr("Refresh")
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Refresh telemetry (R / Space)")
                    fontSize: 12
                    onClicked: backend.refresh()
                }
            }

            // 2. Segmented Navigation Tabs
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 40
                radius: Math.min(8, theme.radius)
                color: theme.cardBackground
                border.color: theme.border
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 3
                    spacing: 4

                    Repeater {
                        model: [
                            { name: "Overview (1)", idx: 0 },
                            { name: "Thermals & Fans (2)", idx: 1 },
                            { name: "Power & Battery (3)", idx: 2 },
                            { name: "Video Transcoder (4)", idx: 3 }
                        ]

                        OmarchyButton {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.preferredWidth: 1
                            text: modelData.name
                            active: win.activeTab === modelData.idx
                            onClicked: win.activeTab = modelData.idx
                        }
                    }
                }
            }

            // 3. Tab Content Area
            StackLayout {
                id: tabStack
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: win.activeTab

                // === TAB 0: OVERVIEW ===
                GridLayout {
                    columns: 2
                    uniformCellWidths: true
                    rowSpacing: 14
                    columnSpacing: 14

                    // Box 1: GPU Hybrid State
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: theme.cardBackground
                        border.color: theme.border
                        border.width: 1
                        radius: theme.radius

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 12

                            Text {
                                text: "GPU Hybrid Graphics"
                                font.family: win.uiFont
                                font.pixelSize: 15
                                font.bold: true
                                color: theme.accent
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: "Intel UHD 630"; font.family: win.uiFont; font.pixelSize: 12; color: theme.muted; Layout.fillWidth: true }
                                Text { text: qsTr("Primary · Active"); font.family: win.monoFont; font.pixelSize: 12; color: theme.foreground }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: "AMD Radeon Pro 5300M"; font.family: win.uiFont; font.pixelSize: 12; color: theme.muted; Layout.fillWidth: true }
                                Rectangle {
                                    radius: Math.min(4, theme.radius)
                                    color: theme.background
                                    implicitWidth: gpuBadgeText.implicitWidth + 14
                                    implicitHeight: 22
                                    Text {
                                        id: gpuBadgeText
                                        anchors.centerIn: parent
                                        text: backend.gpuStatus === "suspended" ? "D3cold" : "D0"
                                        font.family: win.monoFont
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: backend.gpuStatus === "suspended" ? theme.green : theme.yellow
                                    }
                                }
                            }

                            Text {
                                text: "The AMD dGPU sleeps at 0 W when idle and wakes automatically for external displays or heavy compute."
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                                font.family: win.uiFont
                                font.pixelSize: 12
                                color: theme.muted
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    // Box 2: Thermals & Cooling
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: theme.cardBackground
                        border.color: theme.border
                        border.width: 1
                        radius: theme.radius

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 12

                            Text {
                                text: "Thermals & Fan Speed"
                                font.family: win.uiFont
                                font.pixelSize: 15
                                font.bold: true
                                color: theme.accent
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: "CPU"; font.family: win.uiFont; font.pixelSize: 13; color: theme.muted; Layout.fillWidth: true }
                                Text { text: backend.cpuTemp + " °C"; font.family: win.monoFont; font.pixelSize: 13; color: theme.foreground }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: "GPU"; font.family: win.uiFont; font.pixelSize: 13; color: theme.muted; Layout.fillWidth: true }
                                Text { text: backend.gpuTemp + " °C"; font.family: win.monoFont; font.pixelSize: 13; color: theme.foreground }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: qsTr("Fans"); font.family: win.uiFont; font.pixelSize: 13; color: theme.muted; Layout.fillWidth: true }
                                Text {
                                    text: backend.fan1Rpm + " / " + backend.fan2Rpm + " RPM"
                                    font.family: win.monoFont
                                    font.pixelSize: 13
                                    color: theme.foreground
                                }
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    // Box 3: Battery Protection
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: theme.cardBackground
                        border.color: theme.border
                        border.width: 1
                        radius: theme.radius

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 12

                            Text {
                                text: "Battery Protection"
                                font.family: win.uiFont
                                font.pixelSize: 15
                                font.bold: true
                                color: theme.accent
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: "State"; font.family: win.uiFont; font.pixelSize: 13; color: theme.muted; Layout.fillWidth: true }
                                Text { text: backend.batteryCapacity + "% · " + backend.batteryStatus; font.family: win.monoFont; font.pixelSize: 12; color: theme.foreground }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: "Charge limit"; font.family: win.uiFont; font.pixelSize: 13; color: theme.muted; Layout.fillWidth: true }
                                Text { text: backend.chargeLimit + "%"; font.family: win.monoFont; font.pixelSize: 13; color: theme.accent }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10
                                OmarchyButton {
                                    text: qsTr("80% limit")
                                    active: backend.chargeLimit === 80
                                    Layout.fillWidth: true
                                    onClicked: backend.setChargeLimit(80)
                                }
                                OmarchyButton {
                                    text: qsTr("Full charge")
                                    active: backend.chargeLimit === 100
                                    Layout.fillWidth: true
                                    onClicked: backend.setChargeLimit(100)
                                }
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    // Box 4: Audio & Security
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: theme.cardBackground
                        border.color: theme.border
                        border.width: 1
                        radius: theme.radius

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 12

                            Text {
                                text: "Audio & Touch ID"
                                font.family: win.uiFont
                                font.pixelSize: 15
                                font.bold: true
                                color: theme.accent
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                Text { text: qsTr("PipeWire DSP"); font.family: win.uiFont; font.pixelSize: 12; color: theme.muted }
                                Text { text: qsTr("6-channel speakers + microphone"); font.family: win.uiFont; font.pixelSize: 13; color: theme.foreground; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                Text { text: qsTr("Touch ID"); font.family: win.uiFont; font.pixelSize: 12; color: theme.muted }
                                Text { text: qsTr("fprintd bridge"); font.family: win.uiFont; font.pixelSize: 13; color: theme.foreground }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                Text { text: qsTr("Touch Bar"); font.family: win.uiFont; font.pixelSize: 12; color: theme.muted }
                                Text { text: qsTr("Native firmware keys"); font.family: win.uiFont; font.pixelSize: 13; color: theme.foreground }
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }
                }

                // === TAB 1: THERMALS & FANS ===
                Rectangle {
                    color: theme.cardBackground
                    border.color: theme.border
                    border.width: 1
                    radius: theme.radius

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 16

                        Text {
                            text: "Fan Curve Presets"
                            font.family: win.uiFont
                            font.pixelSize: 17
                            font.bold: true
                            color: theme.accent
                        }

                        Text {
                            text: "The fans are driven by t2-fancontrol following temperatures directly from the Apple T2 SMC hwmon interface."
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            font.family: win.uiFont
                            font.pixelSize: 13
                            color: theme.muted
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 12
                            rowSpacing: 12

                            OmarchyButton {
                                text: "Quiet Preset (~2500 RPM)"
                                Layout.fillWidth: true
                                onClicked: backend.setFanPreset("quiet")
                            }
                            OmarchyButton {
                                text: "Balanced Preset (~3500 RPM)"
                                Layout.fillWidth: true
                                onClicked: backend.setFanPreset("balanced")
                            }
                            OmarchyButton {
                                text: "Max Cooling (~5000 RPM)"
                                Layout.fillWidth: true
                                onClicked: backend.setFanPreset("max")
                            }
                            OmarchyButton {
                                text: "Native SMC Curve"
                                Layout.fillWidth: true
                                primary: true
                                onClicked: backend.setFanPreset("auto")
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }
                }

                // === TAB 2: BATTERY & POWER ===
                Rectangle {
                    color: theme.cardBackground
                    border.color: theme.border
                    border.width: 1
                    radius: theme.radius

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 16

                        Text {
                            text: "Battery Charge Threshold"
                            font.family: win.uiFont
                            font.pixelSize: 17
                            font.bold: true
                            color: theme.accent
                        }

                        Text {
                            text: "Controls the Apple T2 SMC charge limiter. Setting 80% cuts charging current to 0 uA to preserve battery cycle life."
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            font.family: win.uiFont
                            font.pixelSize: 13
                            color: theme.muted
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16

                            OmarchyButton {
                                text: "Set 80% Healthy Limit"
                                active: backend.chargeLimit === 80
                                Layout.fillWidth: true
                                onClicked: backend.setChargeLimit(80)
                            }
                            OmarchyButton {
                                text: "Set 100% Full Charge"
                                active: backend.chargeLimit === 100
                                Layout.fillWidth: true
                                onClicked: backend.setChargeLimit(100)
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }
                }

                // === TAB 3: VIDEO TRANSCODER ===
                Rectangle {
                    color: theme.cardBackground
                    border.color: theme.border
                    border.width: 1
                    radius: theme.radius

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 16

                        Text {
                            text: "Apple T2 Hardware Video Transcoder (AVE)"
                            font.family: win.uiFont
                            font.pixelSize: 17
                            font.bold: true
                            color: theme.accent
                        }

                        Text {
                            text: "Converts video files directly on the Apple T2 coprocessor silicon using hevc_v4l2m2m. The x86 CPU and AMD dGPU stay idle."
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            font.family: win.uiFont
                            font.pixelSize: 13
                            color: theme.muted
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Rectangle {
                                Layout.fillWidth: true
                                height: 38
                                color: theme.background
                                border.color: theme.border
                                border.width: 1
                                radius: Math.min(4, theme.radius)

                                TextInput {
                                    id: filePathInput
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    font.family: win.monoFont
                                    font.pixelSize: 13
                                    color: theme.foreground
                                    selectByMouse: true
                                    clip: true
                                }
                            }

                            OmarchyButton {
                                text: "Browse..."
                                onClicked: fileDialog.open()
                            }
                        }

                        FileDialog {
                            id: fileDialog
                            title: "Select Video File"
                            onAccepted: filePathInput.text = selectedFile.toString().replace("file://", "")
                        }

                        OmarchyButton {
                            text: backend.isTranscoding ? "Transcoding on Apple T2..." : "Start T2 H.265 Transcode"
                            primary: !backend.isTranscoding
                            Layout.fillWidth: true
                            enabled: !backend.isTranscoding && filePathInput.text.length > 0
                            onClicked: backend.transcodeT2(filePathInput.text, "")
                        }

                        Text {
                            text: backend.transcodeStatus
                            visible: text.length > 0
                            font.family: win.uiFont
                            font.pixelSize: 13
                            font.bold: true
                            color: theme.accent
                        }

                        Item { Layout.fillHeight: true }
                    }
                }
            }
        }

        // Help Overlay Modal
        Rectangle {
            anchors.fill: parent
            visible: win.helpVisible
            color: theme.background
            radius: theme.radius

            MouseArea { anchors.fill: parent; onClicked: win.helpVisible = false }

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 14

                Text {
                    text: "Keyboard Shortcuts"
                    font.family: win.uiFont
                    font.bold: true
                    font.pixelSize: 18
                    color: theme.accent
                    Layout.alignment: Qt.AlignHCenter
                }

                Text { text: "1, 2, 3, 4 — Switch sections"; font.family: win.uiFont; color: theme.foreground }
                Text { text: "R or Space — Refresh telemetry"; font.family: win.uiFont; color: theme.foreground }
                Text { text: "Q — Quit"; font.family: win.uiFont; color: theme.foreground }
                Text { text: "? — Toggle this help"; font.family: win.uiFont; color: theme.foreground }

                OmarchyButton {
                    text: "Close (?)"
                    Layout.alignment: Qt.AlignHCenter
                    onClicked: win.helpVisible = false
                }
            }
        }
    }
}
