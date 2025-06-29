Dim intX, intY
Dim n=0
Dim num
Import "zm.luae" //导入插件,只需执行一次
zm.Init  //初始化插件,只需执行一次
Do While true

rem z
//开始游戏
FindPic 0, 0, 0, 0, "Attachment:kaishi.png", "000000", 0, 0.8, intX, intY
Goto a
rem z1
//丢骰子
FindPic 0, 0, 0, 0, "Attachment:diutouzi.png", "000000", 0, 0.8, intX, intY
If intX >-1 then
    TracePrint "丢骰子，坐标是"&intX&","&intY
    goto b
Else
    TracePrint "不在梦境内"
    
End If
FindPic 0, 0, 0, 0, "Attachment:diutouzi2.png", "000000", 0, 0.8, intX, intY
If intX >-1 then
    TracePrint "丢骰子，坐标是"&intX&","&intY
    goto b
Else
    TracePrint "不在梦境内"
    
End If
rem z2
//第一格为招募
FindPic 0, 0, 0, 0, "Attachment:zhaomu.png","000000",0, 0.8, intX, intY    
goto c
//第一格为事件
FindPic 0, 0, 0, 0, "Attachment:likai.png","000000",0, 0.8, intX, intY    
goto d
//第一格为事件后续
FindPic 0, 0, 0, 0, "Attachment:maozhua.png","000000",0, 0.7, intX, intY
goto e
//第一格为战斗
FindPic 0, 0, 0, 0, "Attachment:zhandou.png","000000",0, 0.7, intX, intY
goto f
//放弃游戏
FindPic 0, 0, 0, 0, "Attachment:fangqi.png","000000",0, 0.8, intX, intY
goto h

rem a
//找到开始游戏图片
FindPic 0, 0, 0, 0, "Attachment:kaishi.png","000000",0, 0.8, intX, intY
If intX >-1 then
    TracePrint "开始游戏，坐标是"&intX&","&intY
    //点击开始游戏
    Touch 139, 997, 100 
    Delay 500
    //点击招募1
    Touch 278, 957, 100
    Delay 500
    Touch 509, 535, 100
    Delay 500
    Touch 112, 214, 100
    Delay 500
    //点击招募2
    Touch 249, 956, 100
    Delay 500
    Touch 509, 535, 100
    Delay 500
    Touch 112, 214, 100
    Delay 300
    //点击进入游戏
    Touch 139, 997, 100 
    Delay 300

Else
    TracePrint "不在开始界面"
    Goto z1
    
End If

FindPic 0, 0, 0, 0, "Attachment:zhaomu1.png","000000",0, 0.8, intX, intY
If intX >-1 then
    TracePrint "招募1，坐标是"&intX&","&intY
    //点击招募1
    Touch 278, 957, 100
    Delay 500
    Touch 509, 535, 100
    Delay 500
    Touch 112, 214, 100
    Delay 500
    //点击招募2
    Touch 249, 956, 100
    Delay 500
    Touch 509, 535, 100
    Delay 500
    Touch 112, 214, 100
    Delay 300
    //点击进入游戏
    Touch 139, 997, 100 
    Delay 300
Else
    TracePrint "不在招募1"
End If

FindPic 0, 0, 0, 0, "Attachment:zhaomu2.png","000000",0, 0.8, intX, intY
If intX >-1 then
    TracePrint "招募2"&intX&","&intY
    //点击招募1
    Touch 278, 957, 100
    Delay 500
    Touch 509, 535, 100
    Delay 500
    Touch 112, 214, 100
    Delay 500
    //点击招募2
    Touch 249, 956, 100
    Delay 500
    Touch 509, 535, 100
    Delay 500
    Touch 112, 214, 100
    Delay 300
    //点击进入游戏
    Touch 139, 997, 100 
    Delay 300
Else
    TracePrint "招募2"
End If

Delay 12000
Goto z1




Rem b


//识别步数
num = SmartOcr(55,933,79,980)



//定义坐标变量（需根据实际需求赋值）
If  104 > num +0 then
    TracePrint "第二回合放弃游戏"
    Touch 100, 200, 300
    Delay 300
    Touch 234, 796, 300
    Delay 1300
    goto h
Else
    TracePrint "第一回合"
End If
//找到丢骰子图片
FindPic 0, 0, 0, 0, "Attachment:diutouzi.png","000000",0, 0.8, intX, intY
If intX >-1 then
    TracePrint "丢骰子，坐标是"&intX&","&intY
    //自选一个骰子，走一步
    Touch 129, 1141, 300
   	
    Delay 500
    //进入第一格
    Touch 192, 1113, 300
    Delay 3000
	Touch 368, 831, 500
Else
    TracePrint "不在梦境"
    Goto z2
End If

rem c
//第一格为招募
FindPic 0, 0, 0, 0, "Attachment:zhaomu.png","000000",0, 0.8, intX, intY
If intX >-1 then
    TracePrint "招募，坐标是"&intX&","&intY
    //招募第一个角色
    Touch 509, 535, 100
    Delay 300
    Touch 112, 214, 100
    Delay 300
Else
    TracePrint "不在招募"
    
End If


rem d
//第一格为事件
FindPic 0, 0, 0, 0, "Attachment:likai.png","000000",0, 0.8, intX, intY
If intX >-1 then
    TracePrint "事件中，坐标是"&intX&","&intY
    //点击选项二
    Touch 312, 1052, 100
    Delay 300
    Touch 234, 796, 100
    Delay 300
Else
    TracePrint "不在事件"
    
End If

rem e
//第一格为事件后续
FindPic 0, 0, 0, 0, "Attachment:maozhua.png","000000",0, 0.7, intX, intY
If intX >-1 then
    TracePrint "找到猫爪，坐标是"&intX&","&intY
    //点击离开
    Touch 90, 1119, 100
    Delay 300
    Touch 234, 796, 300
	Delay 300
Else
    TracePrint "没有猫抓"
    
End If


rem f
//第一格为战斗
FindPic 0, 0, 0, 0, "Attachment:zhandou.png","000000",0, 0.7, intX, intY
If intX >-1 then
    TracePrint "开始战斗，坐标是"&intX&","&intY
    //点击开始战斗
    Touch 140, 1115, 100
    Delay 300
Else
    TracePrint "不在战斗中"
    
End If

//进入战斗
FindPic 0, 0, 0, 0, "Attachment:zhineng.png","000000",0, 0.7, intX, intY
If intX >-1 then
    TracePrint "自动战斗，坐标是"&intX&","&intY
    //点击开始战斗
    Touch 63, 482, 100
    Delay 300
    Touch 63, 1000, 100
    Delay 300
Else
    TracePrint "不在战斗中"
    
End If

//战斗胜利结算
FindPic 0, 0, 0, 0, "Attachment:zhandoujieshu.png","000000",0, 0.6, intX, intY
If intX >-1 then
    TracePrint "战斗结算，坐标是"&intX&","&intY
    //点击开始战斗
    Touch 63, 482, 100
    Delay 500
    Touch 124, 1147, 100
    Delay 300
    Touch 63, 482, 100
    Delay 500
    Touch 124, 1147, 100
    Delay 300
Else
    TracePrint "不在战斗中"
    
    
End If

 



rem h
//放弃游戏
FindPic 0, 0, 0, 0, "Attachment:fangqi.png","000000",0, 0.8, intX, intY
If intX >-1 then
    TracePrint "放弃游戏，坐标是"&intX&","&intY
    //放弃游戏
    Touch 157, 988, 300
    Delay 300
    Touch 234, 796, 300
    Delay 300
Else
    TracePrint "找不到放弃"
End If

//结算奖励
FindPic 0, 0, 0, 0, "Attachment:jiesuan.png","000000",0, 0.8, intX, intY
If intX >-1 then
    TracePrint "结算界面，坐标是"&intX&","&intY
    //结算奖励
    Touch 139, 633, 300
    Delay 300
    Touch 234, 796, 300
    Delay 300
Else
    TracePrint "找不到结算"
End If

    If n>=10000 Then
        //当循环条件成立的时候，离开循环体
        Exit do
    End if
    n = n + 1

Loop
