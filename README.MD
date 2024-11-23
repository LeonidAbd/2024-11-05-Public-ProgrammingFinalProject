# Programming final project

University of Europe for Applied Sciences  
B.Sc. Software Engieering sem.2  
Programming  
Professor: *Mehmet Kutlay Kocer*

Participants:  
* Leonid Abdrakhmanov  
* Miras Nuraly  

## Infrastructure

The project is the implementation of the game of CHESS, using the tkinter graphical user interface.

##### Files:
- **main.py**
  - creates the Application object, and runs its' inner command.
- **application.py**
  - creates the Application class, uses the tkinter GUI library, and uses the ChessEngine object to find the positions of the pieces.
- **chess_engine.py**
  - creates the ChessEngine class, which works using 64-bit integer numbers, with support of bitwise operations.

## Installation

### Installing | Option 1
Using git, clone the repository to your computer. Run the command line or shell, and run the following command:
```bash
git clone https://github.com/LeonidAbd/2024-11-05-Public-ProgrammingFinalProject.git
```
It will place the directory `./2024-11-05-Public-ProgrammingFinalProject` in your destination directory.

### Installing | Option 2

On the main GitHub page of the project, click the `Code / Download ZIP` . After you get the ZIP array of the directory, unzip it to your computer.
### PyCharm install
When you have your project installed, you might want to use the PyCharm IDE to run it.  

In the IDE, use `File / Open` , and select the project containing directory. Choose the "Trust the source of the project" option, and it is set.

Then, you can set the Virtual Environment to the one mentioned in the project. Press `Ctrl+Shift+A` , and find the `Switch Python Interpreter` action. Then, enter the `Add New Interpreter / Add Local Interpreter` , in the shwed line press the `Virtualenv Environment / Existing / Interpreter` , and choose the `venv\Scripts\python.exe` file.

After that, it may take some time for an interpreter to run, however, the venv is set successfully.
### Running through the .cmd file
You can see the `main.cmd` file in the repository. So, you can simply run the file, which executes the following command:
```
".\venv\Scripts\python.exe" main.py
```