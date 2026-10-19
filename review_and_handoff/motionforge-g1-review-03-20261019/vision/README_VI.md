# Vision QC đã dùng được qua9router

Model route `ag/gemini-3.8-flash-high` **có đọc ảnh thật**. Hai phép thử độc lập về đường gọi: DIRECT_IMAGE_RECEIPT.json và HELPER_LIVE_RECEIPT.json, đềuHTTP200, đọc đúng code ngẫu nhiên và6thuộc tính hình/màu/sốlượng. VERIFICATION.json ghi7/7checks. Response modelhiển thị `gemini-3.8-flash-n`, local9routerusage ghi `gemini-3.8-flash-high`; report giữ cả hai, khôngđổi route/fallback.

Hermes đã cài vision_analyze và video_analyze. Một thử nghiệm native vision toolmessage với capabilityoverride chỉ trongprocess đã timeout90s; chưa có answer nhận về. Vì vậy **không sửa globalconfig để bật một đường chưa được chứng minh**. ConfigSHA giữ `442333a3092b6349f54aaae495e7bed0b6b7fc15ffe87c653b3a2b867a2feb05`. Cóusage phát sinh sautimeout nhưng không đủ bind câu trả lời cho request; timeout không bảo đảm server đã hủy.

Đường dùng được ngay cho sessionGemini: gọi `motionforge_vision_qc.py` qua terminal. Helper gửi pixels trong usermessage đến cùngroute, trả structuredJSON cùng ảnhhash/path/labels/usage. Không phụ thuộc client đoáncapability; khôngmodel/accountoverride; khônglưu secret.

```powershell
& 'C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe' -B 'C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-03-20261019/vision/motionforge_vision_qc.py' --image 'C:/absolute/source-frame.png' --label 'source S0061 f0043' --image 'C:/absolute/cast-reference.png' --label 'CAST E1 immutable reference' --image 'C:/absolute/output-frame.png' --label 'candidate S0061 f0043' --out 'C:/absolute/new-invocation/qc/S0061-f0043.json'
```

Dùng paths thật sauG1mediaapproval. Up to8images/12MB mỗirequest là giới hạnpayloadhelper, khôngtrần dựán. Mộtreceiptpath chỉghi1lần; khi sửa ảnh dùng newreceipt. Credentials từNINEROUTER_API_KEY nếu có hoặc localgateway activekey, khônginra. Có `--question-file` UTF-8 để chỉrõ rubric/roles/events. Responseanalysis có thểUNKNOWN; exit0 chỉtransportOK, **khôngqualityPASS**.

QC-loop sau khi mởmedia: source+CAST+candidatecùngfid → lưuissues/frame/region/severity → phânloại identity/mask/pose/contact/prop/cut → sửa đúnginput/consumer → invalidate descendants → renderlại phầnảnhhưởng → review cùngfixture vàheldout. Không dùng mộtmodeltựchấmPASS thay rootreview.

Helperchỉxem ảnh đượcgửi, không ngheaudio và không tựxemtoànvideo. Để kiểm motion, giữ indexed denseframe sequences của event windows, comparisonclipsplayable vàtemporalmetrics; sampledfames vẫn khôngthay continuousclip/audio review. Nativevideo/audio giữUNKNOWN tới khi có actualtoolproof; khônggắn nhãn đã xemnghe. Không tạo fullpilot/master khiG1chưađượcduyệt.

Root tạohelper mới; khôngupdate/installmodelweights, khôngsửaHermesglobalconfig hoặc9routerruntime. `NATIVE_TOOL_TIMEOUT.json` giữ limitation, khôngchefailurebằngdirectPASS.
