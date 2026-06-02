# KVRB v4 재deposit 실행 가이드 (Daniel 전용)

> 작성 2026-06-02. 목적: 원고(v4)와 Zenodo·GitHub(현재 v3)의 불일치 해소 = DiB 제출 전 유일 blocker.
> Claude 준비 완료분: .gitignore 보강·v4 패키지 zip 빌드·.zenodo.json 갱신·push 목록·안전감사.
> 아래는 **Daniel 계정·클릭이 필요한 부분만** 단계화. 되돌릴 수 없는 공개라 클릭은 본인.

---

## 0. 현재 상태 요약

| 항목 | 상태 |
|---|---|
| DiB 원고 자체 | **제출 준비 완료** (critical 0, ~85% Accept/Minor) |
| 원고가 기술하는 데이터 | **v4** (노인 DL 앵커 재보정: low 85%→35%, real 37%) |
| Zenodo/GitHub 공개분 | **v3** (DOI 10.5281/zenodo.20484546) ← 불일치 |
| **유일 No-Go** | **v4를 GitHub+Zenodo에 재deposit** → 새 v4 DOI 확보 |

Claude가 이미 처리한 것:
- `.gitignore` 보강 — `results_v4/*.csv`·`results_xmodel_N2000/*.csv` 공개 rescue 추가, 정답키(`human_reread_key.csv`)·FILLED 시트·원자료·1M parquet은 계속 비공개 (검증 완료)
- v4 공개 패키지 zip 빌드: `_archive/KVRB_zenodo_upload_v4.zip` (3.9MB, 166파일, 비밀 0건 감사 통과)
- `.zenodo.json` notes에 노인실태조사 2023 앵커 반영

---

## 1. GitHub push (GitHub Desktop 권장)

repo: `https://github.com/kncop0526-star/korea-victimization-risk-benchmark`

push될 파일 (Claude 확정, 모두 공개 안전):
- 코드: `src/recalibrate_elderly_dl.py`·`validate_nonelderly_joint.py`·`crossmodel_extract.py`·`validate_residual_magnitude_match.py`·`build_human_reread_sheet.py`·`score_human_reread.py`
- v4 결과: `results_v4/`(F2·F4·F5·F6·F7 png + 집계 csv/txt/json)·`results_xmodel_N2000/`
- 결과 txt/csv: `results/elderly_dl_recalibration.txt`·`nonelderly_joint_bound.txt`·`residual_magnitude_match.*`
- 원고: `manuscript/KVRB_DataInBrief.{md,docx}`·`KVRB_Data_Descriptor_manuscript.docx`·`KVRB_data_descriptor_submission.md`·`Cover_letter.md`·`Title_page.md`
- docs: `human_coding_protocol.md`·`평정자_지침_README.md`·`v4_deposit_runbook.md`(이 파일)
- 메타: `.gitignore`·`CITATION.cff`·`config/anchors/digital_literacy.csv`
- 평정자 빈 시트: `results/human_reread_rater{1,2,3}.xlsx` (합성텍스트만, 선택사항 — 빼고 싶으면 stage에서 해제)

**자동 제외 확인됨** (push 안 됨): 1M parquet·원자료(노인실태조사·디지털격차)·`human_reread_key.csv`·`*_FILLED.xlsx`·내부노트(`manuscript/_*`·`EXTERNAL_*`)·`config/local_paths.json`·로그

절차:
1. GitHub Desktop에서 repo 열기 → 변경된 39개 파일 확인
2. 좌하단에 비밀/원자료 없는지 눈으로 한 번 더 확인 (위 "자동 제외" 목록이 안 보여야 정상)
3. Commit (메시지 예: `v4: recalibrate elderly DL anchor (노인실태조사 2023), add v4 validation outputs`)
4. **Push origin**
5. **Release 발행**: Releases → Draft a new release → Tag `v1.1-submission` → Publish

> repo가 아직 Private면 Settings → General → Danger Zone → Make public 먼저.

---

## 2. Zenodo 새 버전 발행 → v4 DOI

기존 record(DOI 10.5281/zenodo.20484546)에서 **"New version"** 발행. 두 경로 중 택1:

**경로 A — GitHub 연동(이미 연동돼 있으면 가장 쉬움):**
- 1번에서 Release를 발행하면 Zenodo가 자동으로 새 버전을 아카이브하고 새 DOI를 만듭니다.
- Zenodo가 `.zenodo.json`(Claude가 v4로 갱신함)을 읽어 메타데이터 자동 채움 → 내용 확인 후 **Publish**.

**경로 B — 수동 업로드(연동 안 돼 있으면):**
- Zenodo 로그인 → 기존 KVRB record → **New version**
- 기존 파일 삭제 후 `_archive/KVRB_zenodo_upload_v4.zip` 업로드 (또는 outputs 폴더의 동일 zip)
- 메타데이터: 라이선스 CC-BY-4.0, 저자 Lee Chihwa·ORCID 0009-0009-6959-1797 (기존값 유지) → **Publish**

> 1M 합성파일·원자료는 패키지에 **불포함**이 의도된 설계(코드+앵커로 재현, 원자료는 출처기관 약관). `.zenodo.json` description에 이미 명시됨.

발행 후 **새 v4 DOI를 복사**해서 Claude에게 전달.

---

## 3. (DOI 받은 뒤) Claude가 처리

새 v4 DOI를 주면 Claude가 다음을 일괄 갱신 후 DiB docx 재빌드:
- `manuscript/KVRB_DataInBrief.{md,docx}` — Spec Table + Data Availability 2곳 DOI 교체
- `manuscript/KVRB_data_descriptor_submission.md` §6 Data availability (SD 보류본도 동기화)
- `CITATION.cff` — `doi:` v4로 교체 + `version: 1.1.0` + `date-released` 갱신
- 갱신 후 GitHub 재push 1회 (CITATION·원고만)

---

## 4. DiB 온라인 제출 (Daniel)

Elsevier Editorial Manager (Data in Brief) → 갱신된 `KVRB_DataInBrief.docx` + Cover letter 업로드.

---

## 체크리스트 (제출 직전)

- [ ] GitHub public + Release `v1.1-submission` 발행
- [ ] push 변경분에 비밀/원자료 0건 (자동 제외 확인)
- [ ] Zenodo 새 버전 Publish → v4 DOI 확보
- [ ] (Claude) Spec Table·Data Availability·CITATION DOI v4 교체 + docx 재빌드
- [ ] DiB EM 제출

---

## (선택) human coding 트랙

DiB엔 비필수. 강하게 가려면: `results/human_reread_rater{1,2,3}.xlsx` 3명 평정 → `score_human_reread.py` 채점 → 결과 강하면 Scientific Data v2 트랙으로 승격. 지침은 `docs/평정자_지침_README.md`·`docs/human_coding_protocol.md`.
