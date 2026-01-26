#include <QApplication>
#include <QWidget>
#include <QLabel>
#include <QVBoxLayout>
#include <QTcpSocket>
#include <QDebug>

class OverlayWindow : public QWidget {
public:
    OverlayWindow(QWidget *parent = nullptr) : QWidget(parent) {
        // 设置窗口属性：无边框、置顶、透明背景
        setWindowFlags(Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint | Qt::Tool);
        setAttribute(Qt::WA_TranslucentBackground);
        
        // 设置简单的布局
        auto layout = new QVBoxLayout(this);
        statusLabel = new QLabel("Waiting for AI Engine...", this);
        statusLabel->setStyleSheet("color: white; font-weight: bold; font-size: 16px; background-color: rgba(0, 0, 0, 150); padding: 10px; border-radius: 5px;");
        layout->addWidget(statusLabel);
        
        // 初始化 Socket
        socket = new QTcpSocket(this);
        connect(socket, &QTcpSocket::readyRead, this, &OverlayWindow::onReadyRead);
        connect(socket, &QTcpSocket::connected, [this](){
            statusLabel->setText("Connected to AI Engine");
        });
        connect(socket, &QTcpSocket::disconnected, [this](){
            statusLabel->setText("Disconnected");
        });

        // 尝试连接本地 Python 服务 (默认端口 9999)
        socket->connectToHost("127.0.0.1", 9999);
    }

private slots:
    void onReadyRead() {
        QByteArray data = socket->readAll();
        // TODO: 解析 JSON 数据并更新 UI
        statusLabel->setText("Recv: " + QString::fromUtf8(data));
    }

private:
    QLabel *statusLabel;
    QTcpSocket *socket;
};

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    OverlayWindow window;
    window.resize(300, 100);
    window.move(100, 100); // 初始位置
    window.show();

    return app.exec();
}
