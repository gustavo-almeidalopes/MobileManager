from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout, QMessageBox
from database import Session, SimCard, Log
from dialogs import SimCardDialog

class SimTab(QWidget):
    def __init__(self):
        super().__init__()
        self.session = Session()
        self.current_user = "admin"
        self._build_ui()
        self.apply_filters()

    def _build_ui(self):
        layout = QVBoxLayout()
        fl = QFormLayout()
        self.status_filter = QComboBox(); self.status_filter.addItems(["Todos","Ativo","Bloqueado","Roubado/Furtado"])
        self.op_filter = QLineEdit()
        fl.addRow("Status:", self.status_filter)
        fl.addRow("Operadora:", self.op_filter)
        layout.addLayout(fl)

        btn = QPushButton("Aplicar Filtros"); btn.clicked.connect(self.apply_filters)
        layout.addWidget(btn)

        self.table = QTableWidget(); self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID","ICCID","Operadora","Status"])
        layout.addWidget(self.table)

        self.result_count = QLabel(); layout.addWidget(self.result_count)

        hl = QHBoxLayout()
        for name,fn in [("Adicionar",self.add),("Editar",self.edit),("Excluir",self.delete)]:
            b=QPushButton(name);b.clicked.connect(fn); hl.addWidget(b)
        layout.addLayout(hl)

        self.setLayout(layout)

    def apply_filters(self):
        q=self.session.query(SimCard)
        st=self.status_filter.currentText()
        if st!="Todos": q=q.filter(SimCard.status==st)
        op=self.op_filter.text()
        if op: q=q.filter(SimCard.operadora.like(f"%{op}%"))
        res=q.all(); self._update_table(res)

    def _update_table(self,res):
        self.table.setRowCount(len(res))
        for i,s in enumerate(res):
            self.table.setItem(i,0,QTableWidgetItem(str(s.id)))
            self.table.setItem(i,1,QTableWidgetItem(s.iccid or ""))
            self.table.setItem(i,2,QTableWidgetItem(s.operadora or ""))
            self.table.setItem(i,3,QTableWidgetItem(s.status or ""))
        self.result_count.setText(f"Resultados: {len(res)}")

    def add(self):
        dlg=SimCardDialog(self)
        if dlg.exec_():
            d=dlg.get_data(); new=SimCard(**d)
            self.session.add(new); self.session.commit(); self.log("adicionar", new.id); self.apply_filters()

    def edit(self):
        i=self.table.currentRow();
        if i<0: QMessageBox.warning(self,"Aviso","Selecione um chip."); return
        sid=int(self.table.item(i,0).text()); s=self.session.query(SimCard).get(sid)
        dlg=SimCardDialog(self,s)
        if dlg.exec_():
            for k,v in dlg.get_data().items(): setattr(s,k,v)
            self.session.commit(); self.log("editar", s.id); self.apply_filters()

    def delete(self):
        i=self.table.currentRow();
        if i<0: QMessageBox.warning(self,"Aviso","Selecione um chip."); return
        sid=int(self.table.item(i,0).text())
        if QMessageBox.question(self,"Confirmação","Tem certeza?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            s=self.session.query(SimCard).get(sid)
            self.session.delete(s); self.session.commit(); self.log("excluir", sid); self.apply_filters()

    def log(self,a,d):
        e=Log(usuario=self.current_user,acao=a,detalhes=str(d))
        self.session.add(e); self.session.commit()
