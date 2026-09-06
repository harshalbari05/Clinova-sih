"""Timeline builder for MedicalDocument and ExtractedData entities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.timeline.builders.base import DraftTimelineEvent
from app.timeline.date_utils import parse_clinical_date

if TYPE_CHECKING:
    from app.models.medical_document import MedicalDocument


class DocumentTimelineBuilder:
    """Extracts verifiable, source-backed events from uploaded medical records and structured extraction."""

    @classmethod
    def build_events(cls, documents: list[MedicalDocument]) -> list[DraftTimelineEvent]:
        """Convert medical documents and their structured extraction data into DraftTimelineEvents."""
        events: list[DraftTimelineEvent] = []

        for doc in documents:
            patient_id = doc.patient_id
            doc_id = doc.id
            consultation_id = doc.consultation_id

            # Parse baseline document date
            doc_date = doc.document_date
            doc_date_precision = "EXACT" if doc_date else "UNKNOWN"

            # Check if structured extraction is present
            extracted_data = getattr(doc, "extracted_data", None)
            extracted_json: dict[str, Any] = (
                extracted_data.extracted_json
                if extracted_data and extracted_data.extracted_json
                else {}
            )

            hospital_name = extracted_json.get("hospital_or_clinic_name")
            facility_label = f" at {hospital_name}" if hospital_name else ""

            # 1. Hospital Admission
            admission_raw = extracted_json.get("admission_date")
            if admission_raw:
                parsed_adm, adm_precision = parse_clinical_date(admission_raw)
                events.append(
                    DraftTimelineEvent(
                        patient_id=patient_id,
                        consultation_id=consultation_id,
                        medical_document_id=doc_id,
                        event_type="HOSPITAL_ADMISSION",
                        title=f"Hospital Admission{facility_label}",
                        description=f"Inpatient admission documented on {admission_raw}",
                        event_date=parsed_adm,
                        date_precision=adm_precision,
                        source_type="MEDICAL_DOCUMENT",
                        source_id=str(doc_id),
                        evidence=f"Admission Date: {admission_raw}",
                        source_page=1,
                        verification_status="SOURCE_CONFIRMED",
                        metadata={"hospital": hospital_name},
                    )
                )

            # 2. Hospital Discharge
            discharge_raw = extracted_json.get("discharge_date")
            if discharge_raw:
                parsed_dis, dis_precision = parse_clinical_date(discharge_raw)
                events.append(
                    DraftTimelineEvent(
                        patient_id=patient_id,
                        consultation_id=consultation_id,
                        medical_document_id=doc_id,
                        event_type="HOSPITAL_DISCHARGE",
                        title=f"Hospital Discharge{facility_label}",
                        description=f"Inpatient discharge documented on {discharge_raw}",
                        event_date=parsed_dis,
                        date_precision=dis_precision,
                        source_type="MEDICAL_DOCUMENT",
                        source_id=str(doc_id),
                        evidence=f"Discharge Date: {discharge_raw}",
                        source_page=1,
                        verification_status="SOURCE_CONFIRMED",
                        metadata={"hospital": hospital_name},
                    )
                )

            # 3. Laboratory Results
            lab_results = extracted_json.get("laboratory_results", [])
            for lab in lab_results:
                if isinstance(lab, dict):
                    t_name = lab.get("test_name", "Laboratory Test").strip()
                    val = str(lab.get("value", "")).strip()
                    unit = lab.get("unit") or ""
                    ref_range = lab.get("reference_range")
                    flag = lab.get("abnormal_flag_as_documented")
                    evidence = lab.get("evidence") or f"{t_name}: {val} {unit}".strip()
                    page = lab.get("source_page")
                    test_date_raw = lab.get("test_date")

                    if test_date_raw:
                        ev_date, precision = parse_clinical_date(test_date_raw)
                    else:
                        ev_date, precision = doc_date, doc_date_precision

                    desc_parts = [f"{t_name}: {val} {unit}".strip()]
                    if ref_range:
                        desc_parts.append(f"Ref Range: {ref_range}")
                    if flag:
                        desc_parts.append(f"Flag: {flag}")

                    events.append(
                        DraftTimelineEvent(
                            patient_id=patient_id,
                            consultation_id=consultation_id,
                            medical_document_id=doc_id,
                            event_type="LAB_RESULT",
                            title=f"Lab Result: {t_name}",
                            description=" | ".join(desc_parts),
                            event_date=ev_date,
                            date_precision=precision,
                            source_type="MEDICAL_DOCUMENT",
                            source_id=str(doc_id),
                            evidence=evidence,
                            source_page=page,
                            verification_status="SOURCE_CONFIRMED",
                            metadata={
                                "test_name": t_name,
                                "value": val,
                                "unit": unit,
                                "reference_range": ref_range,
                                "abnormal_flag": flag,
                            },
                        )
                    )

            # 4. Prescribed Medications
            medications = extracted_json.get("medications", [])
            for med in medications:
                if isinstance(med, dict):
                    m_name = med.get("name_as_written", "Medication").strip()
                    dose = med.get("dose_as_written")
                    freq = med.get("frequency_as_written")
                    dur = med.get("duration_as_written")
                    route = med.get("route_as_written")
                    evidence = med.get("evidence") or m_name
                    page = med.get("source_page")

                    desc_parts = [m_name]
                    if dose:
                        desc_parts.append(dose)
                    if freq:
                        desc_parts.append(freq)
                    if dur:
                        desc_parts.append(dur)
                    if route:
                        desc_parts.append(route)

                    events.append(
                        DraftTimelineEvent(
                            patient_id=patient_id,
                            consultation_id=consultation_id,
                            medical_document_id=doc_id,
                            event_type="MEDICATION",
                            title=f"Medication: {m_name}",
                            description=" — ".join(desc_parts),
                            event_date=doc_date,
                            date_precision=doc_date_precision,
                            source_type="MEDICAL_DOCUMENT",
                            source_id=str(doc_id),
                            evidence=evidence,
                            source_page=page,
                            verification_status="SOURCE_CONFIRMED",
                            metadata={
                                "name": m_name,
                                "dose": dose,
                                "frequency": freq,
                                "duration": dur,
                                "route": route,
                                "is_uncertain": med.get("is_uncertain", False),
                            },
                        )
                    )

            # 5. Documented Diagnoses / Conditions
            diagnoses = extracted_json.get("diagnoses_or_conditions_as_documented", [])
            for diag in diagnoses:
                if isinstance(diag, str) and diag.strip():
                    events.append(
                        DraftTimelineEvent(
                            patient_id=patient_id,
                            consultation_id=consultation_id,
                            medical_document_id=doc_id,
                            event_type="DIAGNOSIS_DOCUMENTED",
                            title=f"Documented Diagnosis: {diag.strip()[:60]}",
                            description=f"Explicitly documented in clinical record: {diag.strip()}",
                            event_date=doc_date,
                            date_precision=doc_date_precision,
                            source_type="MEDICAL_DOCUMENT",
                            source_id=str(doc_id),
                            evidence=diag.strip(),
                            source_page=1,
                            verification_status="SOURCE_CONFIRMED",
                            metadata={"raw_diagnosis": diag.strip()},
                        )
                    )

            # 6. Symptoms
            symptoms = extracted_json.get("symptoms_as_documented", [])
            for sym in symptoms:
                if isinstance(sym, str) and sym.strip():
                    events.append(
                        DraftTimelineEvent(
                            patient_id=patient_id,
                            consultation_id=consultation_id,
                            medical_document_id=doc_id,
                            event_type="SYMPTOM",
                            title=f"Documented Symptom: {sym.strip()[:60]}",
                            description=f"Symptom explicitly noted in document: {sym.strip()}",
                            event_date=doc_date,
                            date_precision=doc_date_precision,
                            source_type="MEDICAL_DOCUMENT",
                            source_id=str(doc_id),
                            evidence=sym.strip(),
                            source_page=1,
                            verification_status="SOURCE_CONFIRMED",
                            metadata={"raw_symptom": sym.strip()},
                        )
                    )

            # 7. Imaging Findings
            imaging = extracted_json.get("imaging_findings", [])
            for img in imaging:
                if isinstance(img, str) and img.strip():
                    events.append(
                        DraftTimelineEvent(
                            patient_id=patient_id,
                            consultation_id=consultation_id,
                            medical_document_id=doc_id,
                            event_type="IMAGING",
                            title=f"Imaging Finding: {img.strip()[:60]}",
                            description=f"Documented imaging/radiology impression: {img.strip()}",
                            event_date=doc_date,
                            date_precision=doc_date_precision,
                            source_type="MEDICAL_DOCUMENT",
                            source_id=str(doc_id),
                            evidence=img.strip(),
                            source_page=1,
                            verification_status="SOURCE_CONFIRMED",
                            metadata={"imaging_finding": img.strip()},
                        )
                    )

            # 8. Documented Procedures & Surgeries
            procedures = extracted_json.get("procedures", [])
            for proc in procedures:
                if isinstance(proc, str) and proc.strip():
                    is_surgery = any(
                        w in proc.lower() for w in ("surgery", "operation", "ectomy", "plasty", "otomy")
                    )
                    ev_type = "SURGERY" if is_surgery else "PROCEDURE"
                    events.append(
                        DraftTimelineEvent(
                            patient_id=patient_id,
                            consultation_id=consultation_id,
                            medical_document_id=doc_id,
                            event_type=ev_type,
                            title=f"Documented {ev_type.capitalize()}: {proc.strip()[:60]}",
                            description=f"Procedure explicitly recorded in document: {proc.strip()}",
                            event_date=doc_date,
                            date_precision=doc_date_precision,
                            source_type="MEDICAL_DOCUMENT",
                            source_id=str(doc_id),
                            evidence=proc.strip(),
                            source_page=1,
                            verification_status="SOURCE_CONFIRMED",
                            metadata={"procedure": proc.strip()},
                        )
                    )

            # 9. Documented Allergies
            allergies = extracted_json.get("allergies", [])
            for allergy in allergies:
                if isinstance(allergy, str) and allergy.strip():
                    events.append(
                        DraftTimelineEvent(
                            patient_id=patient_id,
                            consultation_id=consultation_id,
                            medical_document_id=doc_id,
                            event_type="ALLERGY",
                            title=f"Documented Allergy: {allergy.strip()[:60]}",
                            description=f"Allergy explicitly noted in clinical document: {allergy.strip()}",
                            event_date=doc_date,
                            date_precision=doc_date_precision,
                            source_type="MEDICAL_DOCUMENT",
                            source_id=str(doc_id),
                            evidence=allergy.strip(),
                            source_page=1,
                            verification_status="SOURCE_CONFIRMED",
                            metadata={"allergy": allergy.strip()},
                        )
                    )

            # 10. Follow-up Recommendations
            follow_up = extracted_json.get("follow_up_instructions_as_documented")
            if isinstance(follow_up, str) and follow_up.strip():
                events.append(
                    DraftTimelineEvent(
                        patient_id=patient_id,
                        consultation_id=consultation_id,
                        medical_document_id=doc_id,
                        event_type="FOLLOW_UP",
                        title="Documented Follow-up Recommendation",
                        description=follow_up.strip(),
                        event_date=doc_date,
                        date_precision=doc_date_precision,
                        source_type="MEDICAL_DOCUMENT",
                        source_id=str(doc_id),
                        evidence=follow_up.strip(),
                        source_page=1,
                        verification_status="SOURCE_CONFIRMED",
                        metadata={"follow_up": follow_up.strip()},
                    )
                )

        return events
