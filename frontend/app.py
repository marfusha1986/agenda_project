import sys
from PySide6.QtWidgets import (QApplication,QWidget,QLabel,QVBoxLayout,QHBoxLayout,QPushButton,QMessageBox,
                               QLineEdit,QListWidget,QListWidgetItem,QCalendarWidget)
from PySide6.QtCore import Qt,QDate
import requests

class AgendaApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.fetch_tasks()


    def initUI(self):
        self.setWindowTitle("Minimalist Ajanda & Disiplin Takipçisi")
        self.setGeometry(900,900,1000,900)

        # Modern ve şık bir görünüm için QSS (Stil) tanımlıyoruz
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QLabel {
                color: #89b4fa;
                font-weight: bold;
                font-size: 14px;
            }
            QCalendarWidget QWidget {
                background-color: #313244;
                color: #cdd6f4;
            }
            QCalendarWidget QToolButton {
                color: #cdd6f4;
                background-color: #45475a;
                border-radius: 4px;
                margin: 2px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #585b70;
            }
            QListWidget {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #45475a;
            }
            QListWidget::item:selected {
                background-color: #45475a;
                color: #89b4fa;
                border-radius: 4px;
            }
            QLineEdit {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px;
                color: #cdd6f4;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            #DeleteButton {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
            #DeleteButton:hover {
                background-color: #eba0ac;
            }
        """)

        # Ana Düzen (Yan yana: Sol taraf Takvim, Sağ taraf Görev Paneli)
        main_layout = QHBoxLayout(self)

        # --- SOL TARAF: Takvim ---
        left_layout = QVBoxLayout()
        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        left_layout.addWidget(QLabel("Tarih Seçimi"))
        left_layout.addWidget(self.calendar)
        main_layout.addLayout(left_layout, 1)

        # --- SAĞ TARAF: Görev Listesi ve Kontroller ---
        right_layout = QVBoxLayout()

        self.label = QLabel("Görev Listesi")
        right_layout.addWidget(self.label)

        self.task_list_widget = QListWidget(self)
        right_layout.addWidget(self.task_list_widget)

        # Yeni Görev Girişi
        self.task_input = QLineEdit(self)
        self.task_input.setPlaceholderText("Seçilen tarih için görev yazın...")
        right_layout.addWidget(self.task_input)

        # Butonlar Paneli
        btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Görev Ekle", self)
        self.btn_add.clicked.connect(self.add_task)
        btn_layout.addWidget(self.btn_add)

        # Ertele Butonu
        self.btn_postpone = QPushButton("Ertele (+1 Gün)", self)
        self.btn_postpone.setStyleSheet("background-color: #fab387; color: #1e1e2e;")
        self.btn_postpone.clicked.connect(self.postpone_task)
        btn_layout.addWidget(self.btn_postpone)

        self.btn_delete = QPushButton("Seçileni Sil", self)
        self.btn_delete.setObjectName("DeleteButton")
        self.btn_delete.clicked.connect(self.delete_task)
        btn_layout.addWidget(self.btn_delete)

        self.btn_fetch = QPushButton("Yenile", self)
        self.btn_fetch.clicked.connect(self.fetch_tasks)
        btn_layout.addWidget(self.btn_fetch)

        right_layout.addLayout(btn_layout)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)


    def add_task(self):
            title = self.task_input.text().strip()
            if not title:
                QMessageBox.warning(self,"Uyarı","Görev Başlığı boş olamaz!")
                return

            #Takvimden seçilen tarih alıp YYYY-MM-DD formatına çevir
            selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")

            if not selected_date:
                selected_date = QDate.currentDate().toString("yyyy-MM-dd")
    
            #FastAPI backend'in beklediği veri formatı
            payload = {
                "title": title,
                "due_date": selected_date,
                "is_recurring": 0,
                "category": "Genel"
            }
    
            try:
                #Istek atarken header (Content-type) bilgisini açıkça belirtsin
                headers = {"Content-Type":"application/json"}
                response = requests.post("http://127.0.0.1:8000/tasks/",json=payload,headers=headers)

                if response.status_code in [200,201]:
                    self.task_input.clear()
                    self.fetch_tasks() #Listeyi anında güncelle
    
                else:
                    QMessageBox.warning(self,"Hata",f"Görev eklenemedi! Kod:{response.status_code}")
            except Exception as e:
                QMessageBox.critical(self,"Bağlanti Hatası",f"API'ye ulaşılamıyor: \n{e}")


    def fetch_tasks(self):
        print("-> fetch_tasks çağrıldı, API'ye istek atılıyor...")
        try:
            response = requests.get("http://127.0.0.1:8000/tasks/")
            print(f"<- API Yanıt Kodu: {response.status_code}")
            print(f"<- Gelen Veri: {response.text}")
            if response.status_code == 200:
                tasks = response.json()
                self.task_list_widget.clear()

                for task in tasks:
                    #Backendden gelen verinin yapısına göre başlık alanını yazdır
                    title = task.get("title") or task.get("task_title") or str(task)
                    task_id = task.get("id")
                     #Veritabanındakı gerce id,Oracle farklı satırlara atabilir diye
                    due_date = task.get("due_date")
                    if not due_date or due_date == "None":
                        due_date = "Tarihsiz"

                    # Listeye öğe eklerken PyQt'nin kendi içine veri (setData/UserRole) saklanacak
                    item = QListWidgetItem(f"📅 [{due_date}] -> {title}")
                    item.setData(Qt.UserRole,task_id) #Gerçek B eleman ID

                    self.task_list_widget.addItem(item)

                self.label.setText(f"Toplam görev sayısı: {len(tasks)}")
            else:
                print(f"⚠️ Sunucu 200 dışı kod döndürdü: {response.status_code}")
                QMessageBox.warning(self,"Hata","Backend'den veri alınamadı.")
        except Exception as e:
            print(f"❌ Kritik Bağlantı Hatası: {e}")
            QMessageBox.critical(self,"Bağlantı Hatası",f"API'ye ulasılamıyor \n{e}")

    def postpone_task(self):
            current_item = self.task_list_widget.currentItem()
            if not current_item:
                QMessageBox.warning(self,"Uyarı","Lütfen ertelemek için listeden bir görev seçiniz'")
                return
    
            task_id = current_item.data(Qt.UserRole)
    
            from datetime import datetime,timedelta
    
            selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
    
            payload =  {
                "due_time": selected_date
            }
    
            try:
                #Backende güncelleme Endpointi
                response = requests.patch(f"http://127.0.0.1:8000/tasks/{task_id}",json=payload)
                if response.status_code in [200,204]:
                    self.fetch_tasks()
                else:
                    print(f"Erteleme hatası kod: {response.status_code}, detay: {response.text}")
                    QMessageBox.warning(self,"Hata",f"Görev ertelenemedi! Kod:{response.status_code}")
            except Exception as e:
                QMessageBox.critical(self,"Bağlantı Hatası",f"API,ye ulaşılamıyor:\n{e}")
    

    def delete_task(self):
        selected_row = self.task_list_widget.currentItem()
        if not selected_row:
            QMessageBox.critical(self,"Uyarı","Lütfen silmek istediğiniz görevi seçiniz!")
            return

        from PySide6.QtCore import Qt 
        #Doğrudan satır indeksi yerine,seçilen öğenin DB ID'si
        task_id = selected_row.data(Qt.UserRole)
       
        try:
            response = requests.delete(f"http://127.0.0.1:8000/tasks/{task_id}")

            if response.status_code in [200,204]:
                self.fetch_tasks() #Listeyi güncelle
            else:
                QMessageBox.warning(self,"Uyarı",f"Görev silinmedi! Kod:{response.status_code}")
        except Exception as e:
            QMessageBox.critical(self,"Bağlantı Hatası",f"API'ye ulaşılamıyor:\n{e}")

    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AgendaApp()
    ex.show()
    sys.exit(app.exec())