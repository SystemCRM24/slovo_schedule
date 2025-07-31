import React, { useCallback, useEffect, useMemo, useState } from "react";
import CustomModal from "../ui/Modal";
import { Button, FormControl, FormSelect, InputGroup, Alert, Form } from "react-bootstrap";

import { useDayContext } from "../../contexts/Day/provider";
import useSchedules from "../../hooks/useSchedules";
import useSpecialist from "../../hooks/useSpecialist.js";
import { getDateWithTime, getTimeStringFromDate, isIntervalValid, isNewScheduleIntervalValid } from "../../utils/dates.js";
import { useChildrenContext } from "../../contexts/Children/provider.jsx";
import apiClient, { constants } from "../../api/index.js";
import AutoCompleteInput from "../../components/ui/AutoCompleteInput/index.jsx";
import { useContext } from "react";
import { AppContext } from "../../contexts/App/context.js";


const EditAppointmentModal = ({ id, show, setShow, startDt, endDt, patientId, patientType, status, oldpatientId, showModalEdit, setShowModalEdit }) => {
    const { specialistId, specialist } = useSpecialist();
    const [appointment, setAppointment] = useState({
        id: id,
        status: status,
        patientId: patientId,
        patientType: patientType,
        start: startDt,
        end: endDt,
        specialist: specialistId,
        old_patient: oldpatientId,
    });

    const { schedule, generalSchedule, setGeneralSchedule, workSchedule } = useSchedules();
    const patients = useChildrenContext();
    const patientName = useMemo(() => patients?.[patientId], [patientId, patients]);
    const day = useDayContext();
    const children = useChildrenContext();
    const dayOfWeek = day.toLocaleString('ru-RU', { weekday: 'long' });
    const dateString = day.toLocaleDateString();
    const [checkbox, setCheckbox] = useState(false);

    const { reloadSchedule, decreaseModalCount } = useContext(AppContext);

    const [record, recordIndex] = useMemo(() => {
        let index = -1;
        for (const record of schedule) {
            index++;
            if (record.start.getTime() === startDt.getTime() && record.end.getTime() === endDt.getTime()) {
                return [record, index];
            }
        }
        return [{}, -1];
    }, [schedule, startDt, endDt]);

    const onDeleteBtnClick = () => {
        (async () => {
            if (checkbox) {
                await apiClient.deleteAppointmentMassive(id);

            } else {
                await apiClient.deleteAppointment(id);
            }
            setShow(false);
            const newSchedule = schedule.filter((item, index) => index !== recordIndex);
            setGeneralSchedule({
                ...generalSchedule,
                [specialistId]: {
                    ...generalSchedule[specialistId],
                    [day]: newSchedule,
                },
            });
            decreaseModalCount();
        })();
    };

    const onModalEditBtnClick = () => {
        setShow(false);
        setShowModalEdit(!showModalEdit);
    }

    const scheduleWithoutCurrentElem = useMemo(() => {
        return schedule.filter((value, index) => index !== recordIndex);
    }, [recordIndex, schedule]);

    const handleInputChange = async (e) => {
        const { name, value } = e.target;
        let newValue;
        if (['start', 'end'].includes(name)) {
            const [hoursString, minutesString] = value.split(':');
            const hours = parseInt(hoursString);
            const minutes = parseInt(minutesString);
            newValue = getDateWithTime(day, hours, minutes);
        } else {
            newValue = value;
        }
        await onChange(name, newValue);
    };

    const onStartChange = async (e) => {
        const [hoursString, minutesString] = e.target.value.split(':');
        const hours = parseInt(hoursString);
        const minutes = parseInt(minutesString);
        newValue = getDateWithTime(day, hours, minutes);
    }

    const onDurationChange = async (e) => {
        const minutes = e.target.value;
        const end = new Date(appointment.start.getTime() + minutes * 60 * 1000);
        await onChange('end', end);
    };

    const handleCheckboxChange = (e) => {
        setCheckbox(e.target.checked);
    };

    const onChange = async (attrName, value) => {
        setAppointment((prev) => ({ ...prev, [attrName]: value }));
    };

    const onSubmit = async (newAppointment = null) => {
        const source = newAppointment || appointment;
        const newRecord = {
            id: source.id,
            start: source.start,
            end: source.end,
            specialist: source.specialist,
            patient: source.patientId,
            code: source.patientType,
            status: source.patientId !== source.old_patient && source.old_patient ? 'replace' : source.status,
            old_patient: source.old_patient,
        };
        const result = await apiClient.updateAppointment(id, newRecord);
        if (result) {
            const newSchedule = schedule.map((item, index) => {
                if (index === recordIndex) {
                    return {
                        ...newRecord,
                        patient: {
                            id: appointment.patientId,
                            type: appointment.patientType
                        }
                    }
                } else {
                    return item;
                }
            })
            setGeneralSchedule({
                ...generalSchedule,
                [specialistId]: {
                    ...generalSchedule[specialistId],
                    [day]: newSchedule,
                }
            });
            reloadSchedule();
            setShow(false);
        }
    };

    const defaultSelectValues = useMemo(() => [15, 30, 45, 60, 90, 120, 130], []);

    const selectOptions = useMemo(() => {
        return defaultSelectValues.map((value) => (
            <option value={value} key={`duration_${value}`}>
                {value} минут
            </option>
        ));
    }, [defaultSelectValues]);

    const [start, setStart] = useState(getTimeStringFromDate(appointment.start));
    const [duration, setDuration] = useState((appointment.end - appointment.start) / 60000);

    useEffect(
        () => {
            const [hoursString, minutesString] = start.split(':');
            const hours = parseInt(hoursString);
            const minutes = parseInt(minutesString);
            const newStart = getDateWithTime(day, hours, minutes);
            let newEnd = newStart;
            if (!isNaN(newStart)) {
                newEnd = new Date(newStart.getTime() + duration * 60 * 1000);
            }
            onChange('start', newStart);
            onChange('end', newEnd);
        },
        [start, duration]
    )

    const isMoved = useMemo(() => {
        for (const a of schedule) {
            if (a.id === id) {
                const changesList = [];
                if (oldpatientId && oldpatientId !== patientId) {
                    changesList.push(`${children[oldpatientId]} заменен на ${patientName}`)
                }
                if (
                    a.old_specialist && a.old_specialist !== Number(specialistId)
                ) {
                    changesList.push(`Специалист изменён на ${specialist.name}`);
                }

                const oldStart = a.old_start ? new Date(a.old_start) : null;
                if (
                    oldStart &&
                    a.start &&
                    !isNaN(oldStart.getTime()) &&
                    !isNaN(a.start.getTime()) &&
                    oldStart.getTime() !== a.start.getTime()
                ) {
                    changesList.push(
                        `Время начала изменено с ${getTimeStringFromDate(oldStart)} на ${getTimeStringFromDate(a.start)}`
                    );
                }

                const oldEnd = a.old_end ? new Date(a.old_end) : null;
                if (
                    oldEnd &&
                    a.end &&
                    !isNaN(oldEnd.getTime()) &&
                    !isNaN(a.end.getTime()) &&
                    oldEnd.getTime() !== a.end.getTime()
                ) {
                    changesList.push(
                        `Время окончания изменено с ${getTimeStringFromDate(oldEnd)} на ${getTimeStringFromDate(a.end)}`
                    );
                }

                if (a.old_code && a.code && a.old_code !== a.code) {
                    changesList.push(`Тип изменён с ${a.old_code} на ${a.code}`);
                }

                return changesList;
            }
        }
        return [];
    }, [id, schedule, appointment]);

    const onRollBack = () => {
        const rba = { ...appointment };
        for (const a of schedule) {
            if (a.id === id) {
                if (a.old_specialist !== null) {
                    rba.specialist = a.old_specialist;
                }
                if (a.old_start !== null) {
                    rba.start = a.old_start;
                }
                if (a.old_end !== null) {
                    rba.end = a.old_end;
                }
                if (a.old_code !== null) {
                    rba.code = a.old_code;
                }
                onSubmit(rba);
            }
        };
    };

    return (
        <CustomModal
            show={show}
            handleClose={() => setShow(false)}
            title={`${specialist.name} - ${patientName} ${patientType} ${dayOfWeek} ${dateString} ${getTimeStringFromDate(startDt)} - ${getTimeStringFromDate(endDt)}`}
            primaryBtnDisabled={!isNewScheduleIntervalValid(appointment, scheduleWithoutCurrentElem, scheduleWithoutCurrentElem, workSchedule.intervals)}
            handlePrimaryBtnClick={() => onSubmit(appointment)}
            primaryBtnText={'Сохранить'}
        >
            <div className="d-flex flex-column align-items-center justify-content-center w-100 h-100 gap-2">
                <div className="d-flex w-100 align-items-center" style={{ gap: "1rem", whiteSpace: "nowrap" }}>
                    <label>Начало занятия</label>
                    <InputGroup hasValidation>
                        <FormControl
                            type={'time'}
                            value={start}
                            name={'start'}
                            onChange={e => setStart(e.target.value)}
                            style={{ textAlign: "center" }}
                            required
                            isInvalid={
                                !appointment.start ||
                                (!!appointment.start && !isNewScheduleIntervalValid(appointment, scheduleWithoutCurrentElem, scheduleWithoutCurrentElem, workSchedule.intervals))
                            }
                        />
                    </InputGroup>
                    <label>Продолжительность</label>
                    <InputGroup hasValidation>
                        <FormControl
                            as={'select'}
                            style={{ textAlign: "center" }}
                            disabled={!appointment.start}
                            required
                            value={duration}
                            onChange={e => setDuration(e.target.value)}
                            isInvalid={
                                appointment.start !== undefined &&
                                (!isIntervalValid(appointment) || !isNewScheduleIntervalValid(appointment, scheduleWithoutCurrentElem, scheduleWithoutCurrentElem, workSchedule.intervals))
                            }
                        >
                            {selectOptions}
                        </FormControl>
                    </InputGroup>
                </div>
                <InputGroup hasValidation>
                    <AutoCompleteInput
                        options={children}
                        name="patientId"
                        isInvalid={['', null, undefined].includes(appointment.patientId)}
                        onChange={async (e) => {
                            await handleInputChange(e);
                        }}
                        value={appointment.patientId}
                    />
                </InputGroup>
                <InputGroup hasValidation>
                    <FormSelect
                        name={'patientType'}
                        isInvalid={['', null, undefined].includes(appointment.patientType)}
                        onChange={async (e) => {
                            await handleInputChange(e);
                        }}
                        value={appointment.patientType}
                    >
                        {Object.entries(constants.listFieldValues.appointment.idByCode)
                            .sort(([aCode], [bCode]) => aCode.localeCompare(bCode, 'en', { sensitivity: 'base' }))
                            .map(([code, id]) => (
                                <option value={code} key={`${day}_interval_${recordIndex}_${code}_opt`}>
                                    {code}
                                </option>
                            ))}
                    </FormSelect>
                </InputGroup>
                <Alert variant="warning" show={isMoved.length > 0}>
                    <div className={"gap-2 d-flex align-items-start"}>
                        <div>
                            {isMoved.map((item, index) => (
                                <div key={index}>{item}<br /></div>
                            ))}
                        </div>
                        <Button
                            variant="outline-dark"
                            style={{ marginLeft: "15px" }}
                            onClick={onRollBack}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-counterclockwise" viewBox="0 0 16 16">
                                <path fill-rule="evenodd" d="M8 3a5 5 0 1 1-4.546 2.914.5.5 0 0 0-.908-.417A6 6 0 1 0 8 2z" />
                                <path d="M8 4.466V.534a.25.25 0 0 0-.41-.192L5.23 2.308a.25.25 0 0 0 0 .384l2.36 1.966A.25.25 0 0 0 8 4.466" />
                            </svg>
                        </Button>
                    </div>
                </Alert>
            </div>
            <div className="d-flex align-items-center w-100 h-100 gap-2 mt-3">
                <Button
                    variant="warning"
                    onClick={onModalEditBtnClick}
                    style={{ paddingRight: "1rem" }}
                >
                    Перенести
                </Button>
                <Button variant="danger" onClick={onDeleteBtnClick}>Удалить</Button>
                <Form.Group className="me-0">
                    <Form.Check
                        type="checkbox"
                        label="Массовое удаление"
                        checked={checkbox}
                        onChange={(e) => handleCheckboxChange(e)}
                    />
                </Form.Group>
            </div>
        </CustomModal>
    );
};

export default EditAppointmentModal;