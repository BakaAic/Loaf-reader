import os
import pickle,base64

from tkinter import *
from tkinter.ttk import *
from tkinter import font
from configparser import ConfigParser

try:
    import keyboard
except ImportError:
    import pip
    pip.main(['install', 'keyboard'])
    import keyboard

_path=os.getcwd()
_bookPath=os.path.join(_path,"books")
if not os.path.exists(_bookPath):
    os.mkdir(_bookPath)

class KeyBoardListener():
    def __init__(self):
        self.queue = []
    
    def putQueue(self,key):
        self.queue.append(key)
    
    def getQueue(self):
        if len(self.queue) == 0:
            return None
        else:
            return self.queue.pop(0)

class BookPage():
    def __init__(self):
        self.page = []
        self.totalPage = 0
    def __getitem__(self,key: int):
        return self.page[key]
    def addPage(self,page: tuple[int,int]):
        self.page.append(page)
        self.totalPage += 1

class Book():
    def __init__(self,book):
        self.bookname = book
        self.bookpath = _bookPath+'//'+book
        self.book = None
        self.openBook()
        self.bookLen = len(self.book)
        self.page = None
        self.mark = 0
        
    def loadPage(self,page):
        self.page = page
    
    def loadMark(self,mark):
        self.mark = mark
    
    def openBook(self):
        try:
            with open(self.bookpath,"r",encoding="utf-8") as f:
                self.book = f.read()
        except UnicodeDecodeError:
            try:
                with open(self.bookpath,"r",encoding="gb2312") as f:
                    self.book = f.read()
            except UnicodeDecodeError:
                try:
                    with open(self.bookpath,"r",encoding="gb18030") as f:
                        self.book = f.read()
                except UnicodeDecodeError:
                    with open(self.bookpath,"r",encoding="gbk",errors="replace") as f:
                        self.book = f.read()

class Reader():
    def __init__(self,keyBoardListener):
        self.keyBoardListener = keyBoardListener
        self.curBook = None
        self.showText = ""
        self.loafMode = False
        self.colorMode = True
        self.switching = False
        self.leftHandMode = False
        self.halfWidthMode = False
        self.jumpWindowStatus = False
        self.bookWindowStatus = False
        self.hideState = False
        self.wordWidth = 150
        self.wordHeight = 10
        self.pos_x = 0
        self.pos_y = 0
        self.curPageNum = 0
    
    def _openBook(self,book):
        return Book(book)
    
    def _loadMark(self,book):
        try:
            config = ConfigParser()
            config.read(os.path.join(_path,"mark.ini"))
            config.sections()
            if book in config.sections():
                try:
                    return int(config[book]["mark"])
                except:
                    return 0
            else:
                config.add_section(book)
                config[book]["mark"] = "0"
                config.write(open(os.path.join(_path,"mark.ini"),"w"))
                return 0
        except:
            return 0
    
    def _loadPage(self,book):
        add_flag=False
        try:
            config = ConfigParser()
            config.read(os.path.join(_path,"mark.ini"))
            if book in config.sections():
                try:
                    return pickle.loads(base64.b64decode(config[book]["page"]))
                except:
                    add_flag=True
            else:
                add_flag=True
        except:
            add_flag=True
        if add_flag:
            if book not in config.sections():
                config.add_section(book)
            bookpage=self._splitPage(self.curBook)
            config[book]["page"] = base64.b64encode(pickle.dumps(bookpage)).decode()
            config.write(open(os.path.join(_path,"mark.ini"),"w"))
            return bookpage
        
    def _splitPage(self,book):
        bookpage=BookPage()
        char_mark=0
        while True:
            curPage=self.calcNumOfPage(book.book,book.bookLen,char_mark)
            if curPage==0:
                return bookpage
            bookpage.addPage((char_mark,curPage))
            char_mark+=curPage

    def _loadBook(self,event):
        book = self.bookList.get(self.bookList.curselection())
        self.curBook = self._openBook(book)
        self._showMsg(f"Loading {book}...")
        self.curBook.loadPage(self._loadPage(book))
        self.curBook.loadMark(self._loadMark(book))
        self._updateShow()
        self._showBook()
        self._updatePage()
        self.bookWindow.destroy()
        self.bookWindowStatus = False
        
    def _showMsg(self,msg):
        self.textList['state'] = 'normal'
        self.textList.delete(1.0, END)
        self.textList.insert(1.0, msg)
        self.textList.see(1.0)
        self.textList['state'] = 'disabled'
        self.root.update()
    
    def _updateShow(self):
        showRange=self.curBook.page.page[self.curBook.mark]
        self.showText = self.curBook.book[showRange[0]:showRange[0]+showRange[1] - (0 if self.curBook.book[showRange[0]+showRange[1]-1] != '\n' else 1)]
    
    def _showBook(self):
        self.textList['state'] = 'normal'
        self.textList.delete(1.0, END)
        self.textList.insert(1.0, self.showText)
        self.textList.see(1.0)
        self.textList['state'] = 'disabled'
    
    def mainWindow(self):
        self.root = Tk()
        self.fonts = font.Font(family='black', size=11)
        self.screenWidth = self.root.winfo_screenwidth() - 600
        self.screenHeight = self.root.winfo_screenheight() - 250
        self.root.title("Loaf Reader (F7:HalfWidth F8:LeftHandLock F9:ChangeColor F10:LoafMode F11:Jump F12:SelectBook))")
        self.root.attributes("-topmost", True)
        self.root.geometry(f"{self.screenWidth}x180+300+{self.screenHeight}")
        self.root.resizable(False, False)
        self.canvas = Canvas(self.root, width=self.screenWidth, height=400, bg="#030303", highlightthickness=0, relief='ridge')
        self.canvas.place(x=0, y=0)
        self._updatePage()
        self.textList = Text(self.root, width=self.wordWidth, height=self.wordHeight+1,font=self.fonts, bg="#030303", fg="#FAFAFA" if self.colorMode else "#0A0A0A", highlightthickness=0, relief='flat'
                             ,selectbackground="#030303",selectforeground="#FAFAFA" if self.colorMode else "#0A0A0A")
        self.textList.place(x=0, y=0)
        self.textList['state'] = 'disabled'
        self.canvas.bind("<ButtonPress-1>", self._dragPress)
        self.canvas.bind("<B1-Motion>", self._dragMotion)
        self.canvas.bind("<ButtonRelease-1>", self._dragRelease)
        self.textList.bind("<ButtonPress-1>", self._dragPress)
        self.textList.bind("<B1-Motion>", self._dragMotion)
        self.textList.bind("<ButtonRelease-1>", self._dragRelease)
        self.root.bind("<Destroy>", self.windowDestroy)
        self.root.after(10, self.eventLoop)
        self.root.mainloop()

    def _updatePage(self):
        if not self.hideState:
            self.canvas.delete('page')
            if self.halfWidthMode:
                self.canvas.create_text(self.screenWidth//2, self.wordWidth*2, text=self._getPage() if self.curBook!=None else 'N/A', font=self.fonts, fill="#FAFAFA" if self.colorMode else "#0A0A0A", anchor='ne',tag='page')
            else:
                self.canvas.create_text(self.screenWidth, self.wordWidth, text=self._getPage() if self.curBook!=None else 'N/A', font=self.fonts, fill="#FAFAFA" if self.colorMode else "#0A0A0A", anchor='ne',tag='page')

    def _getPage(self):
        return f"{self.curBook.mark+1}/{self.curBook.page.totalPage}"

    def windowDestroy(self,*event):
        self.bookMark()
    
    def loafModeSwitch(self):
        self.loafMode = not self.loafMode
        self.switching = True
        
    def leftHandModeSwitch(self):
        self.leftHandMode = not self.leftHandMode
        
    def halfWidthModeSwitch(self):
        self.halfWidthMode = not self.halfWidthMode
        if self.halfWidthMode:
            self.halfWidthWindows()
        else:
            self.fullWidthWindows()
        
    def colorModeSwitch(self):
        self.colorMode = not self.colorMode
        self.colorUpdate()
        
    def colorUpdate(self):
        self._updatePage()
        self.textList['fg'] = "#FAFAFA" if self.colorMode else "#0A0A0A"
        self.textList['selectforeground'] = "#FAFAFA" if self.colorMode else "#0A0A0A"
        if not self.loafMode:
            self.textList['bg'] = "#030303" if self.colorMode else "#FAFAFA"
            self.canvas['bg'] = "#030303" if self.colorMode else "#FAFAFA"
        else:
            self.textList['bg'] = "#030303"
            self.canvas['bg'] = "#030303"
            self.canvas.delete('handler')
            self.canvas.create_rectangle((self.screenWidth//2-7) if self.halfWidthMode else self.screenWidth -7, 0, (self.screenWidth//2) if self.halfWidthMode else self.screenWidth,
                                         15, fill="#FAFAFA" if self.colorMode else "#0A0A0A", outline="#FAFAFA" if self.colorMode else "#0A0A0A",tags='handler')
        self.root.update()
        
    def _loadLibrary(self):
        self.bookList.delete(0, END)
        for book in os.listdir(_bookPath):
            if book.endswith(".txt"):
                self.bookList.insert(END, book)
        
    def selectBook(self):
        self.bookWindowStatus = True
        self.bookWindow = Toplevel()
        self.bookWindow.title("Select Book")
        self.bookWindow.geometry("250x490")
        self.bookWindow.attributes("-topmost", True)
        self.bookWindow.resizable(False, False)
        self.bookList = Listbox(self.bookWindow, width=35, height=27)
        self.bookList.place(x=0, y=0)
        self._loadLibrary()
        self.bookList.bind("<Double-Button-1>", self._loadBook)
        self.bookWindow.focus_set()
    
    def jumpToPage(self):
        self.jumpWindowStatus = True
        self.jumpWindow = Toplevel()
        self.jumpWindow.title("Jump to Page")
        self.jumpWindow.geometry("180x70")
        self.jumpWindow.attributes("-topmost", True)
        self.jumpWindow.attributes("-toolwindow", True)
        self.jumpWindow.resizable(False, False)
        Label(self.jumpWindow, text="Page:").place(x=10, y=10)
        if self.curBook!=None:
            Label(self.jumpWindow, text=f"/{self.curBook.page.totalPage}").place(x=115, y=10)
            self.jumpInput=Entry(self.jumpWindow, width=8)
        else:
            self.jumpInput=Entry(self.jumpWindow, width=15)
        self.jumpInput.place(x=50, y=10)
        self.jumpButton=Button(self.jumpWindow, text="Jump", width=20, command=self._jumpPage)
        self.jumpButton.place(x=18, y=40)
        self.jumpWindow.bind("<Return>", self._jumpPage)
        self.jumpInput.focus_set()
        
    def _jumpPage(self,*event):
        if self.curBook!=None:
            try:
                jumpPage=int(self.jumpInput.get())
                if jumpPage>0 and jumpPage<=self.curBook.page.totalPage:
                    self.curBook.mark = jumpPage - 1
                    self._updateShow()
                    self._showBook()
                    self._updatePage()
                    self.jumpWindow.destroy()
                    self.jumpWindowStatus = False
                else:
                    self.jumpInput.delete(0, END)
            except:
                pass
    
    def _dragMotion(self,event):
        self.root.geometry(f"+{event.x_root-self.pos_x}+{event.y_root-self.pos_y}")
    
    def _dragPress(self,event):
        self.pos_x = event.x
        self.pos_y = event.y + (0 if self.loafMode else 30)
    
    def _dragRelease(self,event):
        self.root.geometry(f"+{event.x_root-self.pos_x}+{event.y_root-self.pos_y}")
    
    def loafWindow(self):
        try:
            self.switching = False
            self.root.overrideredirect(True)
            self.root.attributes("-transparentcolor", '#030303')
            self.canvas.create_rectangle((self.screenWidth//2-7) if self.halfWidthMode else self.screenWidth -7, 0, (self.screenWidth//2) if self.halfWidthMode else self.screenWidth,
                                         15, fill="white", outline="white",tag='handler')
            self.colorUpdate()
        except:
            pass
        
    def fullWindow(self):
        try:
            self.switching = False
            self.root.overrideredirect(False)
            self.root.attributes("-transparentcolor", '#39AF0F')
            self.canvas.delete('handler')
            self.colorUpdate()
            self.root.focus_set()
        except:
            pass
        
    def isFullWidth(self,char):
        unicode_value = ord(char)
        if (unicode_value >= 0xFF01 and unicode_value <= 0xFF5E) or (unicode_value >= 0x0020 and unicode_value <= 0x007E):
            return False
        else:
            return True
    
    def upFloat(self,num):    
        if num-int(num)>0:
            return int(num)+1
        else:
            return int(num)
    
    def calcNumOfPage(self,book,bookLen,curMark):
        num = 0
        linechar = 0
        line = 0
        total = 0
        for i in book[curMark : curMark+ self.wordWidth * self.wordHeight + 1]:
            total += 1
            if i == '\n':
                num += self.wordWidth - self.upFloat(linechar) % self.wordWidth
                line += 1 + (linechar // self.wordWidth)
                linechar = 0
            else:
                if self.isFullWidth(i):
                    num += 1.875
                    linechar += 1.875
                else:
                    num += 1
                    linechar += 1
            if num >= self.wordWidth * self.wordHeight:
                if i == '\n':
                    total -= 1
                break
            if line >= self.wordHeight:
                break
            if total >= bookLen:
                break
        return total
        
    def nextPage(self):
        if self.curBook!=None:
            self.curBook.mark += 1
            if self.curBook.mark >= self.curBook.page.totalPage - 1:
                self.curBook.mark = self.curBook.page.totalPage - 1
            self._updateShow()
            self._showBook()
            self._updatePage()
    
    def prevPage(self):
        if self.curBook!=None:
            self.curBook.mark -= 1
            if self.curBook.mark < 0:
                self.curBook.mark = 0
            self._updateShow()
            self._showBook()
            self._updatePage()
    
    def bookMark(self):
        try:
            config = ConfigParser()
            config.read(os.path.join(_path,"mark.ini"))
            config.sections()
            if self.curBook != None:
                with open(os.path.join(_path,"mark.ini"),"w") as f:
                    config[self.curBook.bookname]["mark"] = str(self.curBook.mark)
                    config.write(f)
        except:
            pass
        
    def show(self):
        if self.hideState:
            self.hideState = False
            self.textList.place(x=0, y=0)
            if self.loafMode:
                self.canvas.create_rectangle((self.screenWidth//2-7) if self.halfWidthMode else self.screenWidth -7, 0, (self.screenWidth//2) if self.halfWidthMode else self.screenWidth, 
                                             15, fill="#FAFAFA" if self.colorMode else "#0A0A0A", outline="#FAFAFA" if self.colorMode else "#0A0A0A",tags='handler')
                self._updatePage()
    
    def hide(self):
        self.canvas.delete('handler')
        if not self.hideState:
            self.hideState = True
            self.textList.place_forget()
            self.canvas.delete('page')
            
    def halfWidthWindows(self):
        self.root.geometry(f"{self.screenWidth//2+20}x360+300+{self.screenHeight-180}")
        self.textList['width'] = self.wordWidth//2
        self.textList['height'] = self.wordHeight*2+1
        if self.loafMode:
            self.canvas.create_rectangle((self.screenWidth//2-7) if self.halfWidthMode else self.screenWidth -7, 0, (self.screenWidth//2) if self.halfWidthMode else self.screenWidth, 
                                             15, fill="#FAFAFA" if self.colorMode else "#0A0A0A", outline="#FAFAFA" if self.colorMode else "#0A0A0A",tags='handler')
        self._updatePage()
    
    def fullWidthWindows(self):
        self.root.geometry(f"{self.screenWidth}x180+300+{self.screenHeight}")
        self.textList['width'] = self.wordWidth
        self.textList['height'] = self.wordHeight+1
        if self.loafMode:
            self.canvas.create_rectangle((self.screenWidth//2-7) if self.halfWidthMode else self.screenWidth -7, 0, (self.screenWidth//2) if self.halfWidthMode else self.screenWidth, 
                                             15, fill="#FAFAFA" if self.colorMode else "#0A0A0A", outline="#FAFAFA" if self.colorMode else "#0A0A0A",tags='handler')
        self._updatePage()
        
    def eventLoop(self):
        key_event=self.keyBoardListener.getQueue()
        if key_event:
            if key_event == "Escape":
                if self.jumpWindowStatus:
                    self.jumpWindow.destroy()
                    self.jumpWindowStatus = False
                elif self.bookWindowStatus:
                    self.bookWindow.destroy()
                    self.bookWindowStatus = False
                else:
                    self.root.destroy()
            elif key_event == "F7":
                self.halfWidthModeSwitch()
            elif key_event == "F8":
                self.leftHandModeSwitch()
            elif key_event == "F9":
                self.colorModeSwitch()
            elif key_event == "F10":
                self.loafModeSwitch()
            elif key_event == "F11":
                if self.jumpWindowStatus:
                    self.jumpWindow.destroy()
                    self.jumpWindowStatus = False
                else:
                    self.jumpToPage()
            elif key_event == "F12":
                if self.bookWindowStatus:
                    self.bookWindow.destroy()
                    self.bookWindowStatus = False
                else:
                    self.selectBook()
            elif key_event == "Left" or (key_event == "A" if self.leftHandMode else False):
                self.prevPage()
            elif key_event == "Right" or (key_event == "D" if self.leftHandMode else False):
                self.nextPage()
            elif key_event == "Up" or (key_event == "W" if self.leftHandMode else False):
                self.show()
            elif key_event == "Down" or (key_event == "S" if self.leftHandMode else False):
                self.hide()
        if self.loafMode:
            if self.switching:
                self.loafWindow()
        else:
            if self.switching:
                self.fullWindow()
        self.root.after(10, self.eventLoop)

keyboard_listen=KeyBoardListener()
keyboard.add_hotkey("F7", keyboard_listen.putQueue, args=["F7"])
keyboard.add_hotkey("F8", keyboard_listen.putQueue, args=["F8"])
keyboard.add_hotkey("F9", keyboard_listen.putQueue, args=["F9"])
keyboard.add_hotkey("F10", keyboard_listen.putQueue, args=["F10"])
keyboard.add_hotkey("F11", keyboard_listen.putQueue, args=["F11"])
keyboard.add_hotkey("F12", keyboard_listen.putQueue, args=["F12"])
keyboard.add_hotkey("Left", keyboard_listen.putQueue, args=["Left"])
keyboard.add_hotkey("Right", keyboard_listen.putQueue, args=["Right"])
keyboard.add_hotkey("Up", keyboard_listen.putQueue, args=["Up"])
keyboard.add_hotkey("Down", keyboard_listen.putQueue, args=["Down"])
keyboard.add_hotkey("Escape", keyboard_listen.putQueue, args=["Escape"])
keyboard.add_hotkey("W", keyboard_listen.putQueue, args=["W"])
keyboard.add_hotkey("S", keyboard_listen.putQueue, args=["S"])
keyboard.add_hotkey("A", keyboard_listen.putQueue, args=["A"])
keyboard.add_hotkey("D", keyboard_listen.putQueue, args=["D"])
reader=Reader(keyboard_listen)
reader.mainWindow()
