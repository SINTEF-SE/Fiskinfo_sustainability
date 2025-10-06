from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItem, QFontMetrics, QStandardItemModel
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate

# Helper classes for gui setup
# MultiComboBox for multiple choice combo box so more than one item can be selected for group boxes (e.g. lenght, gear, species)

#CheckableQCombobox with multiple choices

"""
    Multiple choice ComboBox with checked items display based on:
    https://gis.stackexchange.com/questions/350148/qcombobox-multiple-selection-pyqt5
"""
class MultiComboBox(QComboBox):
    class Delegate(QStyledItemDelegate):
        # Subclass Delegate to increase item line spacing
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(max(20, size.height()))
            return size

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make the combo editable to set a custom text, but readonly
        self.setEditable(True)      # needed to create LineEdit
        self.lineEdit().setReadOnly(True)

        # Catch exit via RETURN key to ensure proper text display
        self.lineEdit().returnPressed.connect(self.update_text)

        # Allow clicks on item's text to perform toggle
        self.view().pressed.connect(self.handle_item_press)

        # Use custom delegate for sizing
        self.setItemDelegate(MultiComboBox.Delegate())

        # Update the text when an item is toggled
        self.model().dataChanged.connect(self.update_text)

    def resizeEvent(self, e):
        # Recompute text to elide *after* resizing so updated width is used
        super().resizeEvent(e)
        self.update_text()

    def get_model(self) -> QStandardItemModel:
        # Perform "cast" on QAbstractItemModel to what QComboBox instantiates
        # to avoid linter complaints about it not being a QStandardItemModel
        model = self.model()
        if isinstance(model, QStandardItemModel):
            return model
        else:
            raise ValueError(f'model is {type(model)}?')

    def handle_item_press(self, index: QModelIndex):
        # Toggle checkbox of clicked on item; triggers dataChanged which updates the text
        item = self.get_model().itemFromIndex(index)
        if item.checkState == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)

    def update_text(self):
        texts = []
        model = self.get_model()
        for i in range(model.rowCount()):
            if model.item(i).checkState() == Qt.CheckState.Checked:
                texts.append(model.item(i).text())
        text = ", ".join(texts)

        # Compute elided text (with "...")
        metrics = QFontMetrics(self.lineEdit().font())
        elided_text = metrics.elidedText(text, Qt.TextElideMode.ElideRight, self.lineEdit().width())
        self.lineEdit().setText(elided_text)
        # print('update_text:', elided_text)

    def add_item(self, text, checked=False, data=None):
        # Add a new "choice" with optional initial check state and data value
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        item.setData(data if data is not None else text)
        self.get_model().appendRow(item)

    def add_items(self, texts, checklist=None, datalist=None):
        # Add a list of new "choices" with optional initial states and data values
        for i, text in enumerate(texts):
            checked = False if not checklist else checklist[i]
            data = None if not datalist else datalist[i]
            self.add_item(text, checked, data)

    def checked_items_data(self):
        # Return a list of the checked items' data values (defaulted to item's text)
        items = []
        model = self.get_model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                items.append(item.data())
        return items

    def checked_items_text(self):
        # Return a list of tuple(text, data) for checked items
        tds = []
        model = self.get_model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                tds.append((item.text(), item.data()))
        return tds

