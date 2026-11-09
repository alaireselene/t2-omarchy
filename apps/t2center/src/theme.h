#pragma once

#include <QFileSystemWatcher>
#include <QObject>
#include <QProcess>
#include <QTimer>

class Theme : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString background READ background NOTIFY changed)
    Q_PROPERTY(QString cardBackground READ cardBackground NOTIFY changed)
    Q_PROPERTY(QString border READ border NOTIFY changed)
    Q_PROPERTY(QString foreground READ foreground NOTIFY changed)
    Q_PROPERTY(QString muted READ muted NOTIFY changed)
    Q_PROPERTY(QString accent READ accent NOTIFY changed)
    Q_PROPERTY(QString accentForeground READ accentForeground NOTIFY changed)
    Q_PROPERTY(QString green READ green NOTIFY changed)
    Q_PROPERTY(QString yellow READ yellow NOTIFY changed)
    Q_PROPERTY(QString red READ red NOTIFY changed)
    Q_PROPERTY(int radius READ radius NOTIFY changed)

public:
    explicit Theme(const QString &currentDirectory = {}, QObject *parent = nullptr, const QString &hyprctl = {});
    ~Theme() override;

    QString background() const { return m_background; }
    QString cardBackground() const { return m_cardBackground; }
    QString border() const { return m_border; }
    QString foreground() const { return m_foreground; }
    QString muted() const { return m_muted; }
    QString accent() const { return m_accent; }
    QString accentForeground() const;
    QString green() const { return m_green; }
    QString yellow() const { return m_yellow; }
    QString red() const { return m_red; }
    int radius() const { return m_radius; }

signals:
    void changed();

private:
    void reload();
    void refreshRounding();

    QString m_directory;
    QString m_background = "#060B1E";
    QString m_cardBackground = "#131a3a";
    QString m_border = "#252e56";
    QString m_foreground = "#ffcead";
    QString m_muted = "#6d7db6";
    QString m_accent = "#FFD60A";
    QString m_green = "#92a593";
    QString m_yellow = "#E9BB4F";
    QString m_red = "#ED5B5A";
    int m_radius = 0;

    QFileSystemWatcher m_watcher;
    QTimer m_debounce;
    QString m_hyprctl;
    QProcess m_roundingProcess;
    QTimer m_roundingPoll, m_roundingTimeout;
};
