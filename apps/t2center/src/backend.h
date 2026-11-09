#pragma once

#include <QObject>
#include <QProcess>
#include <QTimer>

class Backend : public QObject {
    Q_OBJECT
    Q_PROPERTY(int cpuTemp READ cpuTemp NOTIFY updated)
    Q_PROPERTY(int gpuTemp READ gpuTemp NOTIFY updated)
    Q_PROPERTY(int batteryTemp READ batteryTemp NOTIFY updated)
    Q_PROPERTY(int fan1Rpm READ fan1Rpm NOTIFY updated)
    Q_PROPERTY(int fan2Rpm READ fan2Rpm NOTIFY updated)
    Q_PROPERTY(double systemWatts READ systemWatts NOTIFY updated)
    Q_PROPERTY(QString gpuStatus READ gpuStatus NOTIFY updated)
    Q_PROPERTY(QString batteryStatus READ batteryStatus NOTIFY updated)
    Q_PROPERTY(int batteryCapacity READ batteryCapacity NOTIFY updated)
    Q_PROPERTY(int chargeLimit READ chargeLimit NOTIFY updated)
    Q_PROPERTY(bool isTranscoding READ isTranscoding NOTIFY transcodingChanged)
    Q_PROPERTY(QString transcodeStatus READ transcodeStatus NOTIFY transcodingChanged)

public:
    explicit Backend(QObject *parent = nullptr);
    ~Backend() override;

    int cpuTemp() const { return m_cpuTemp; }
    int gpuTemp() const { return m_gpuTemp; }
    int batteryTemp() const { return m_batteryTemp; }
    int fan1Rpm() const { return m_fan1Rpm; }
    int fan2Rpm() const { return m_fan2Rpm; }
    double systemWatts() const { return m_systemWatts; }
    QString gpuStatus() const { return m_gpuStatus; }
    QString batteryStatus() const { return m_batteryStatus; }
    int batteryCapacity() const { return m_batteryCapacity; }
    int chargeLimit() const { return m_chargeLimit; }
    bool isTranscoding() const { return m_isTranscoding; }
    QString transcodeStatus() const { return m_transcodeStatus; }

    Q_INVOKABLE void refresh();
    Q_INVOKABLE void setChargeLimit(int limit);
    Q_INVOKABLE void setFanPreset(const QString &preset);
    Q_INVOKABLE void transcodeT2(const QString &inputPath, const QString &outputPath);

signals:
    void updated();
    void transcodingChanged();

private slots:
    void onStatusReady(int exitCode, QProcess::ExitStatus exitStatus);

private:
    int m_cpuTemp = 0;
    int m_gpuTemp = 0;
    int m_batteryTemp = 0;
    int m_fan1Rpm = 0;
    int m_fan2Rpm = 0;
    double m_systemWatts = 0.0;
    QString m_gpuStatus = "unknown";
    QString m_batteryStatus = "unknown";
    int m_batteryCapacity = 0;
    int m_chargeLimit = 100;
    bool m_isTranscoding = false;
    QString m_transcodeStatus;

    QProcess m_statusProcess;
    QProcess m_actionProcess;
    QProcess m_transcodeProcess;
    QTimer m_timer;
};
