import sys
from PySide6.QtWidgets import (QApplication,QWidget,QLabel,QVBoxLayout,     QHBoxLayout,QPushButton,QMessageBox,
                               QLineEdit,QListWidget,QListWidgetItem,QCalendarWidget,QDialog,QDialogButtonBox)
from PySide6.QtCore import Qt,QDate
from PySide6.QtGui import Qt,QTextCharFormat,QColor
import requests

class AgendaApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.fetch_tasks()
        self.calendar.selectionChanged.connect(self.fetch_tasks)


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
        self.btn_postpone = QPushButton("Ertele", self)
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
        print("-> Tüm görevler yükleniyor ve takvim güncelleniyor...")
        try:
            response = requests.get("http://127.0.0.1:8000/tasks/")
            print(f"<- API Yanıt Kodu: {response.status_code}")
            print(f"<- Gelen Veri: {response.text}")

            if response.status_code == 200:
                tasks = response.json()
                self.task_list_widget.clear()

                #---O an takvimde seçili olan tarihi alıyor
                selected_date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
                selected_date_task = []

                months = {
                    "JAN":1,
                    "FEB":2,
                    "MAR":3,
                    "APR":4,
                    "MAY":5,
                    "JUN":6,
                    "JUL":7,
                    "AUG":8,
                    "SEP":9,
                    "OCT":10,
                    "NOV":11,
                    "DEC":12
                }

                for task in tasks:
                    #Backendden gelen verinin yapısına göre başlık alanını yazdır
                    title = task.get("title") or task.get("task_title") or str(task)
                    task_id = task.get("id")
                     #Veritabanındakı gerce id,Oracle farklı satırlara atabilir diye
                    due_date = task.get("due_date")

                    if not due_date or due_date == "None" or due_date == "Tarihsiz":
                        continue
                    else:
                        #Takvim üzerinde görev olan günü renklendirelim
                        try:
                            normalized_date = ""
                            q_date = None
                            #Oracle formatı kontrolü
                            if "-" in due_date and len(due_date.split("-")) == 3:
                                parts = due_date.split("-")
                                day_part = parts[0]
                                month_str = parts[1].upper()
                                year_part = parts[2]

                                if month_str in months:
                                    day = int(day_part)
                                    month = months[month_str]
                                    #Yıl 26 ise 2026 yap
                                    year = int(year_part)
                                    if year < 100:
                                        year += 2000

                                    q_date = QDate(year,month,day)

                            #Önce QDate ile parse etneye çalışalım
                            
                            if not q_date or not q_date.isValid():
                                q_date = QDate.fromString(due_date,"yyyy-MM-dd")

                            if q_date and q_date.isValid():
                                normalized_date = q_date.toString("yyyy-MM-dd")

                                day_format = QTextCharFormat()
                                day_format.setFontWeight(75)
                                day_format.setForeground(QColor("#ff79c6"))
                                self.calendar.setDateTextFormat(q_date,day_format)

                                 #Eğer görevin tarihi,o an takvimdeki güne uyuyorsa listeye eklemek üzere seçelim
                                if normalized_date == selected_date_str:
                                    selected_date_task.append(task)

                        except Exception as e:
                            print(f"Takvim işaretleme hatası: {e}")

                #Sağ tarafa sadece seçilen günün görevlerini basalım
                for task in selected_date_task:
                    title = task.get("title") or task.get("task_title") or str(task)
                    task_id = task.get("id")
                    due_date = task.get("due_date")

                    #Erteleme sayısı alalım(Backendden)
                    postpone_count = task.get("postpone_count",0)

                    # Disiplin Kuralı: Eğer görev 3 kereden fazla ertelenmişse ekranda uyarı rozeti gösterelim
                    if postpone_count >= 3:
                        display_text = f"⚠️ [{due_date}] {title}  (Çok Ertelendi: {postpone_count} kez!)Disipline sadık kal ve ya görevi sil!"
                    elif postpone_count > 0:
                        display_text = f"📌 [{due_date}] {title}  (Erteleme: {postpone_count})"
                    else:
                        display_text = f"📌 [{due_date}] {title}"


                    # Listeye öğe eklerken PyQt'nin kendi içine veri (setData/UserRole) saklanacak
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole,task_id) #Gerçek B eleman ID

                    self.task_list_widget.addItem(item)

                self.label.setText(f"Tarih {selected_date_str} (Görev: {len(selected_date_task)})")
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

            #---Kullanıcıya yeni tarihi soran mini pencere(DIALOG)---
            dialog = QDialog(self)
            dialog.setWindowTitle("Görevi Ertele")
            dialog.resize(550,750)

            layout = QVBoxLayout(dialog)

            #İçine minik bir takvim koydum
            date_picker = QCalendarWidget(dialog)
            layout.addWidget(date_picker)

            #Kaydet ve İptal butonları
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,dialog)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            #Kullanıcı tarih seçip OK tuşuna basarsa
            if dialog.exec() == QDialog.DialogCode.Accepted:
                q_date = date_picker.selectedDate()
                selected_date = q_date.toString("yyyy-MM-dd")

                print(f"->Seçilen Hedef tarih:{selected_date}")

                if not selected_date:
                    QMessageBox.warning(self, "Uyarı", "Geçerli bir tarih seçilmedi!")
                    return
    
                payload =  {
                "due_date": selected_date
                }
    
            try:
                #Backende güncelleme Endpointi
                response = requests.patch(f"http://127.0.0.1:8000/tasks/{task_id}",json=payload)
                print(f"<-Erteleme yanıt kodu:{response.status_code},Yanıt:{response.text}")

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