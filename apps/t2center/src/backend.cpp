#include "backend.h"

#include <QJsonDocument>
#include <QJsonObject>
#include <QUrl>
#include <QFileInfo>

Backend::Backend(QObject *parent) : QObject(parent) {
    connect(&m_statusProcess, &QProcess::finished, this, &Backend::onStatusReady);

    connect(&m_transcodeProcess, &QProcess::finished, this, [this](int code, QProcess::ExitStatus status) {
        m_isTranscoding = false;
        if (code == 0 && status == QProcess::NormalExit)
            m_transcodeStatus = tr("Encoding completed successfully!");
        else
            m_transcodeStatus = tr("Encoding failed.");
        emit transcodingChanged();
    });

    m_timer.setInterval(2500);
    connect(&m_timer, &QTimer::timeout, this, &Backend::refresh);
    m_timer.start();

    refresh();
}

Backend::~Backend() {
    if (m_statusProcess.state() != QProcess::NotRunning) m_statusProcess.kill();
    if (m_actionProcess.state() != QProcess::NotRunning) m_actionProcess.kill();
    if (m_transcodeProcess.state() != QProcess::NotRunning) m_transcodeProcess.kill();
}

void Backend::refresh() {
    if (m_statusProcess.state() == QProcess::NotRunning) {
        m_statusProcess.start("/usr/libexec/t2-control", {"status"});
    }
}

void Backend::onStatusReady(int exitCode, QProcess::ExitStatus exitStatus) {
    if (exitCode != 0 || exitStatus != QProcess::NormalExit)
        return;

    const auto doc = QJsonDocument::fromJson(m_statusProcess.readAllStandardOutput());
    if (!doc.isObject())
        return;

    const auto obj = doc.object();
    m_cpuTemp = obj.value("cpu_temp_c").toInt();
    m_gpuTemp = obj.value("gpu_temp_c").toInt();
    m_batteryTemp = obj.value("battery_temp_c").toInt();
    m_systemWatts = obj.value("system_watts").toDouble();
    m_gpuStatus = obj.value("gpu_runtime_status").toString();
    m_batteryStatus = obj.value("battery_status").toString();
    m_batteryCapacity = obj.value("battery_capacity").toInt();
    m_chargeLimit = obj.value("charge_limit").toInt();

    const auto fans = obj.value("fans_rpm").toObject();
    m_fan1Rpm = fans.value("fan1_input").toInt();
    m_fan2Rpm = fans.value("fan2_input").toInt();

    emit updated();
}

void Backend::setChargeLimit(int limit) {
    if (m_actionProcess.state() != QProcess::NotRunning)
        return;
    m_actionProcess.start("pkexec", {"/usr/libexec/t2-control", "set-charge-limit", QString::number(limit)});
    m_actionProcess.waitForFinished(3000);
    refresh();
}

void Backend::setFanPreset(const QString &preset) {
    if (m_actionProcess.state() != QProcess::NotRunning)
        return;
    m_actionProcess.start("pkexec", {"/usr/libexec/t2-control", "set-fan-preset", preset});
    m_actionProcess.waitForFinished(3000);
    refresh();
}

void Backend::transcodeT2(const QString &inputUrl, const QString &outputUrl) {
    if (m_isTranscoding)
        return;

    QString input = inputUrl;
    if (input.startsWith("file://")) input = QUrl(inputUrl).toLocalFile();

    QString output = outputUrl;
    if (output.isEmpty()) {
        QFileInfo fi(input);
        output = fi.absolutePath() + "/" + fi.completeBaseName() + "_t2hevc.mp4";
    } else if (output.startsWith("file://")) {
        output = QUrl(outputUrl).toLocalFile();
    }

    m_isTranscoding = true;
    m_transcodeStatus = tr("Transcoding with Apple T2 AVE hardware encoder...");
    emit transcodingChanged();

    m_transcodeProcess.start("ffmpeg", {
        "-hide_banner", "-loglevel", "error",
        "-i", input,
        "-pix_fmt", "nv12",
        "-c:v", "hevc_v4l2m2m",
        "-b:v", "6M",
        "-c:a", "copy",
        "-y", output
    });
}
