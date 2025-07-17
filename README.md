Preparation:
Car： 
1. Python version ≥ 3.8, pip3 install -r requirements-car.txt
2. Please make sure you have run the following command to source the environment:
   ```
   source /opt/ros/humble/setup.bash
   ```
3. Launch cobridge before you run this python file. 

Control Terminal：
1. The python file （control.py）support Both windows and Linux. 
2. Make sure teh python version version ≥ 3.8, and use 'pip3 install pynput' install the dependence. 
3. use python3 control.py to start the control system and start the coStudio. 

How to use: 
1. Upload the 'Car' folder to your car. 
2. Launch cobridge before you start use the python program. 
3. Please make sure you have run the following command to source the environment:
   ```
   source /opt/ros/humble/setup.bash
   ```
4. Install the dependences on your PC(pip3 install -r requirement-pc.txt). 
5. Edit the /Pc/config.yaml, make sure the ip addresss is correct. 
6. Use command 'python3 control.py' to start control. 
7. Open coStudio and connect to your car. Then use the keyboard to control the car.  
