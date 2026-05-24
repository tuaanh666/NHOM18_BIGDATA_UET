# OrbitWars

# 🚀 Kế hoạch 2 tuần — Orbit Wars

> **Cuộc thi:** [Kaggle Orbit Wars](https://www.kaggle.com/competitions/orbit-wars)  
> **Deadline nộp thầy:** 08/06/2026  
> **Mục tiêu score:** ≥ 1000  

---

## 👥 Phân công thành viên

| Thành viên | Vai trò | Màu |
|---|---|---|
| **Member 1** | RL Agent & Training | 🔵 |
| **Member 2** | Environment & Game Logic | 🟢 |
| **Member 3** | Evaluation, Report & Submit | 🟡 |

---

## 📅 Tuần 1 (24/05 – 30/05) — Khởi động & Baseline

### Thứ 7 — 24/05

- [ ] 🔵🟢🟡 Cả nhóm: Đọc rules, setup Kaggle env, clone repo, phân công rõ ràng
- [ ] 🟢 Member 2: Cài `kaggle-environments>=1.28.0`, chạy được `main.py` vs `random`
- [ ] 🟡 Member 3: Setup GitHub repo, branch convention, viết README ban đầu

### Chủ nhật — 25/05

- [ ] 🔵 Member 1: Phân tích observation space, vẽ sơ đồ game flow
- [ ] 🟢 Member 2: Viết visualizer — render bản đồ hành tinh + fleet
- [ ] 🟡 Member 3: Submit agent mẫu lên Kaggle, ghi nhận score ban đầu (~600)

### Thứ 2 — 26/05

- [ ] 🔵 Member 1: Viết hàm orbit prediction (iterative intercept)
- [ ] 🟢 Member 2: Viết Gym wrapper — observation, action, reward cơ bản
- [ ] 🟡 Member 3: Cải thiện heuristic v1: multi-target + sun avoidance

### Thứ 3 — 27/05

- [ ] 🔵 Member 1: Implement PPO baseline với `stable-baselines3`
- [ ] 🟢 Member 2: Hoàn thiện reward function: ship delta + planet capture bonus
- [ ] 🟡 Member 3: Viết `evaluate.py` — tính win rate vs `random`, vs `heuristic`

### Thứ 4 — 28/05

- [ ] 🔵 Member 1: Train PPO 100k steps, so sánh vs heuristic
- [ ] 🟢 Member 2: Fix edge case: comet expiry, sun sweep, tie combat
- [ ] 🟡 Member 3: Submit heuristic v1 lên Kaggle → mục tiêu score **> 800**

### Thứ 5 — 29/05

- [ ] 🔵 Member 1: Reward shaping: future production value, survival bonus
- [ ] 🟢 Member 2: Setup self-play: agent đánh vs chính mình để train
- [ ] 🟡 Member 3: Phân tích replay thua, tìm điểm yếu của heuristic

### Thứ 6 — 30/05

- [ ] 🔵🟢🟡 Cả nhóm: Review tuần 1, merge code vào `main`, demo game
- [ ] 🔵 Member 1: Train PPO 500k steps qua đêm
- [ ] 🟡 Member 3: Bắt đầu outline report IEEE

---

## 📅 Tuần 2 (31/05 – 06/06) — Cải tiến & Hoàn thiện

### Thứ 7 — 31/05

- [ ] 🔵 Member 1: Đánh giá PPO — nếu tốt hơn heuristic thì dùng, nếu không thì tinh chỉnh heuristic cấp 2
- [ ] 🟢 Member 2: Thêm enemy fleet tracking vào scoring function
- [ ] 🟡 Member 3: Viết report — Introduction + Related Work

### Chủ nhật — 01/06

- [ ] 🔵 Member 1: Thêm game phase strategy (early / mid / late weights)
- [ ] 🟢 Member 2: Implement safe angle — vòng tránh mặt trời khi đường bay bị chặn
- [ ] 🟡 Member 3: Submit agent tốt nhất → mục tiêu score **> 1000**

### Thứ 2 — 02/06

- [ ] 🔵 Member 1: Tinh chỉnh hyperparameters: `lr`, `batch_size`, `n_steps`
- [ ] 🟢 Member 2: Tối ưu tốc độ agent, giảm thời gian tính toán mỗi lượt
- [ ] 🟡 Member 3: Viết report — Method + Architecture

### Thứ 3 — 03/06

- [ ] 🔵 Member 1: Thử novelty nếu kịp: Diffusion Policy hoặc AlphaZero approach
- [ ] 🟢 Member 2: Test 4-player FFA mode, điều chỉnh chiến lược tương ứng
- [ ] 🟡 Member 3: Viết report — Experiments + Results

### Thứ 4 — 04/06

- [ ] 🔵 Member 1: Chọn agent cuối cùng: PPO hay heuristic tốt nhất
- [ ] 🟢 Member 2: Clean code — thêm docstring, xóa debug prints
- [ ] 🟡 Member 3: Viết report — Conclusion, chụp ảnh ranking Kaggle

### Thứ 5 — 05/06

- [ ] 🔵🟢🟡 Cả nhóm: Review toàn bộ, test agent lần cuối, kiểm tra report
- [ ] 🟡 Member 3: Submit Kaggle lần cuối, chụp màn hình leaderboard
- [ ] 🟢 Member 2: Finalize GitHub — tag release, cập nhật README

### Thứ 6 — 06/06 *(buffer)*

- [ ] 🔵🟢🟡 Cả nhóm: Fix bug phút chót, chuẩn bị phỏng vấn nhóm
- [ ] 🟡 Member 3: Format report IEEE, export PDF
- [ ] 🔵 Member 1: Chuẩn bị slide giải thích thuật toán cho buổi phỏng vấn

---

## 🏁 Deadline — 08/06/2026

> Nộp thầy đầy đủ 3 thứ:

- [ ] 📄 **Report** — file PDF theo chuẩn IEEE Conference
- [ ] 💻 **Code** — GitHub repo sạch, có README hướng dẫn chạy
- [ ] 🏆 **Ranking** — Screenshot leaderboard Kaggle

---

## 🎯 Mục tiêu score theo từng mốc

| Thời điểm | Mục tiêu | Ghi chú |
|---|---|---|
| 25/05 | ~600 | Agent mẫu gốc |
| 28/05 | > 800 | Heuristic v1 (orbit + sun avoidance) |
| 01/06 | > 1000 | Heuristic v2 + defense + phase |
| 05/06 | > 1200 | PPO hoặc heuristic cấp 2 |

---

## ⚠️ Rủi ro & Dự phòng

| Rủi ro | Giải pháp |
|---|---|
| PPO không hội tụ kịp deadline | Dùng heuristic cải tiến làm submission chính |
| Kaggle submission bị lỗi | Submit sớm từ tuần 1 để có thời gian fix |
| Thiếu thời gian viết report | Viết song song với coding từ 30/05 |
| Score không tăng sau khi submit | Xem replay, phân tích trận thua, điều chỉnh scoring |

---

## 📂 Cấu trúc repo

```
orbit-wars/
├── main.py                  # Agent submit Kaggle
├── agents/
│   ├── heuristic_agent.py
│   └── rl_agent.py
├── environment/
│   ├── gym_wrapper.py
│   ├── reward.py
│   └── visualize.py
├── training/
│   ├── train.py
│   ├── evaluate.py
│   └── config.yaml
├── report/
│   └── report.pdf
├── notebooks/
│   └── orbit_wars_notebook.ipynb
├── PLAN.md
├── requirements.txt
└── README.md
```

---

## 🔗 Tài nguyên

- [Kaggle Orbit Wars](https://www.kaggle.com/competitions/orbit-wars)
- [Notebook mẫu — RL Pipeline](https://www.kaggle.com/code/thisisn0mad/orbit-wars-rl-pipelinepublic)
- [Notebook mẫu — Heuristic Agent scored 1000](https://www.kaggle.com/code/zacharymaronek/orbit-wars-heuristicagent-scored-1000)
- [Local Arena Tool](https://www.kaggle.com/datasets/penguin069/orbit-wars-local-arena)
- [IEEE Conference Template](https://www.ieee.org/conferences/publishing/templates)

---

## 🤝 Quy ước làm việc

```
Branch:   main (stable) | dev | feature/tên-tính-năng
Commit:   [M1] thêm PPO | [M2] fix orbit | [M3] update report
PR:       cần ít nhất 1 người approve trước khi merge vào main
Submit:   mỗi ngày 1 lần lên Kaggle để theo dõi score
```
