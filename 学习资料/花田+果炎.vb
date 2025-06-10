Function 花田()

    花田用时 = Round(TickCount() /60000,1)
    dim 花田1 = false, 花田2 = false, looptime, l = 0

    backWorld

    click 874, 1618//打开小地图
    delay 300
    If Image.OcrText(950, 150, 1010, 350, 0, 1) <> "无名 小镇" Then 
        TracePrint Image.OcrText(950, 150, 1010, 350, 0, 1) & ",不在无名小镇"
        backWorld
        openMap
        tpTown 0
        TracePrint "传送到无名小镇"
        FW.SetTextView "即时信息", "传送到无名小镇", 1400, 0, 520, 30
    Else 
        backWorld
    End If 

    moveMinimap 750,630//走到花田中间


    //收取花田1
    While 花田1 = false
        click 550,800//点击花田1

        looptime = 0
        While Image.OcrText(410, 910, 450, 1000, 0, 1) <> "确定" and looptime < 10
            Delay 200
            looptime = looptime + 1
            traceprint "等待弹出确认窗口"
            FW.SetTextView "即时信息", "等待弹出确认窗口", 1400, 0, 520, 30
        Wend

        If looptime = 10 Then 
            花田1 = True
            TracePrint "--------------------------没收到花田1"
            FW.SetTextView "即时信息", "没收到花田1", 1400, 0, 520, 30
        End If

        If 花田1 = false Then 
            TracePrint "--------------------------采集中"
            FW.SetTextView "即时信息", "采集中", 1400, 0, 520, 30
            If Len(Image.OcrText(550, 1060, 600, 1100, 0, 1)) < 2 Then 
                TracePrint "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1)
                FW.SetTextView "即时信息", "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1), 1400, 0, 520, 30
                l = l + 1
                TracePrint"运行" & Round(TickCount() /60000,1) & "分钟," & "花田重启" & l & "次"
                FW.SetTextView "主窗口", "正在收取花田 1 。花田重启 " & l & " 次", 0, 0, 1400, 30
                restartGame
            Else 
                花田1 = True
                TracePrint "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1)
                FW.SetTextView "即时信息", "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1), 1400, 0, 520, 30
                click 430,960//点击确认收取	
                TracePrint "-----------------------------------------已收取花田1"
                FW.SetTextView ("主窗口", "已收取花田 1", 0, 0, 1400, 30)
            End If
        End If
    Wend




    //收取花田2
    While 花田2 = false
        click 550,1090//点击花田2

        looptime = 0
        While Image.OcrText(410, 910, 450, 1000, 0, 1) <> "确定" and looptime < 10
            Delay 200
            looptime = looptime + 1
            traceprint "等待弹出确认窗口"
            FW.SetTextView "即时信息", "等待弹出确认窗口", 1400, 0, 520, 30
        Wend

        If looptime = 10 Then 
            花田2 = True
            TracePrint "--------------------------没收到花田2"
            FW.SetTextView "即时信息", "没收到花田2", 1400, 0, 520, 30
        End If

        If 花田2 = false Then 
            TracePrint "--------------------------采集中"
            If Len(Image.OcrText(550, 1060, 600, 1100, 0, 1)) < 2 Then 
                TracePrint "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1)
                FW.SetTextView "即时信息", "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1), 1400, 0, 520, 30
                l = l + 1
                TracePrint"运行" & Round(TickCount() /60000,1) & "分钟," & "花田重启" & l & "次"
                FW.SetTextView ("主窗口", "正在收取花田 2 。花田已重启 " & l & " 次", 0, 0, 1400, 30)
                restartGame 
            Else 
                花田2 = True
                TracePrint "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1)
                FW.SetTextView "即时信息", "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1), 1400, 0, 520, 30
                click 430,960//点击确认收取	
                TracePrint "----------------------------------------已收取花田2"
                FW.SetTextView ("即时信息", "已收取花田 2", 1400, 0, 520, 30)
            End If
        End If
    Wend
    花田用时 = Round(TickCount() /60000,1) - 花田用时
    TracePrint"--------------------------花田完成,用时" & 花田用时 & "分钟"
    FW.SetTextView ("主窗口", "花田完成,用时 " & 花田用时 & " 分钟，重启了 " & l & "次", 0, 0, 1400, 30)
End Function

Function 果炎()
    果炎用时 = Round(TickCount() /60000,1)
    dim 果炎果实 = false, looptime, l = 0
    backWorld
    openMap
    tpAnywhere 13//传送到圣树之泉
    moveMinimap 722, 677//走到果树边上
    //收取果炎
    While 果炎果实 = False

        click 450,562//点击果炎
        looptime = 0
        While Image.OcrText(410, 910, 450, 1000, 0, 1) <> "确定" and looptime < 10
            Delay 200
            looptime = looptime + 1
            traceprint "等待弹出确认窗口"
            FW.SetTextView "即时信息", "等待弹出确认窗口", 1400, 0, 520, 30
        Wend

        If looptime = 10 Then 
            果炎果实 = True
            traceprint "--------------------------没收到果炎果实"
            FW.SetTextView "即时信息", "没收到果炎果实" , 1400, 0, 520, 30
        End If

        if 果炎果实 = False then
            if Image.OcrText(550, 850, 600, 1140, 0, 1) = "果炎果实 X100" then
                traceprint "薅到果炎果实了：" & Image.OcrText(530, 830, 600, 1140, 0, 1)
                FW.SetTextView "即时信息", "薅到果炎果实了：" & Image.OcrText(550, 850, 600, 1140, 0, 1), 1400, 0, 520, 30
                click 430,960//点击确认收取	
                TracePrint "----------------------------------------------------------------已收取果炎果实"
                FW.SetTextView "即时信息", "已收果炎果实", 1400, 0, 520, 30
                果炎果实 = True
            Else
                traceprint "果树"  & "没薅到果炎果实：" & Image.OcrText(550, 850, 600, 1140, 0, 1)
                FW.SetTextView "即时信息", "果炎果实"  & "没薅到果炎果实：" & Image.OcrText(550, 850, 600, 1140, 0, 1), 1400, 0, 520, 30
                l = l + 1
                TracePrint "果炎果实已重启" & l & "次。当前正在收取果炎果实 " 
                FW.SetTextView "主窗口", "果炎果实已重启" & l & "次。当前正在收取果炎果实 " , 0, 0, 1400, 30
                restartGame
            End If
        End If
    Wend


    果炎果实 = Round(TickCount() /60000,1) - 果炎果实
    TracePrint"-----------------------------------------------------果炎完成,总用时" & Round(TickCount() /60000,1) & "分钟"
    FW.SetTextView ("主窗口", "果炎果实完成，用时 " & 果炎果实 & " 分钟，重启了 " & l & "次", 0, 0, 1400, 30)
End Function
