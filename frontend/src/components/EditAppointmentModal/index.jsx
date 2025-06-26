import React, { useCallback, useMemo, useState } from "react";
import CustomModal from "../ui/Modal";
import { Button, FormControl, FormSelect, InputGroup, Alert } from "react-bootstrap";

import { useDayContext } from "../../contexts/Day/provider";
import useSchedules from "../../hooks/useSchedules";
import useSpecialist from "../../hooks/useSpecialist.js";
import { getDateWithTime, getTimeStringFromDate, isIntervalValid, isNewScheduleIntervalValid } from "../../utils/dates.js";
import { useChildrenContext } from "../../contexts/Children/provider.jsx";
import apiClient, { constants } from "../../api/index.js";


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
        old_patient: oldpatientId
    });

    const { schedule, generalSchedule, setGeneralSchedule, workSchedule } = useSchedules();
    const patients = useChildrenContext();
    const patientName = useMemo(() => patients?.[patientId], [patientId, patients]);
    const day = useDayContext();
    const children = useChildrenContext();
    const dayOfWeek = day.toLocaleString('ru-RU', { weekday: 'long' });
    const dateString = day.toLocaleDateString();

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

    const onDeleteBtnClick = useCallback(() => {
        (async () => {
            await apiClient.deleteAppointment(id);
            setShow(false);
            const newSchedule = schedule.filter((item, index) => index !== recordIndex);
            setGeneralSchedule({
                ...generalSchedule,
                [specialistId]: {
                    ...generalSchedule[specialistId],
                    [day]: newSchedule,
                },
            });
        })();
    }, [id, setShow, schedule, setGeneralSchedule, generalSchedule, specialistId, day, recordIndex]);

    const onModalEditBtnClick = () => {
        setShow(false)
        setShowModalEdit(!showModalEdit)
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

    const handleSelectInputChange = async (e) => {
        const minutes = e.target.value;
        const end = new Date(appointment.start.getTime() + minutes * 60 * 1000);
        await onChange('end', end);
    };

    const onChange = async (attrName, value) => {
        setAppointment((prev) => ({ ...prev, [attrName]: value }));
    };

    const onSubmit = async () => {
        const newRecord = {
            id: appointment.id,
            start: appointment.start,
            end: appointment.end,
            specialist: appointment.specialist,
            patient: appointment.patientId,
            code: appointment.patientType,
            status: appointment.status,
            old_patient: appointment.old_patient
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
            setShow(false);
        }
    };

    const defaultSelectValues = useMemo(() => [15, 30, 45, 60, 90, 120, 130], []);

    const selectValue = useMemo(() => (appointment.end - appointment.start) / 60000, [appointment]);

    const selectOptions = useMemo(() => {
        const options = defaultSelectValues.map((value) => (
            <option value={value} key={`duration_${value}`}>
                {value} минут
            </option>
        ));
        if (!defaultSelectValues.includes(selectValue)) {
            options.push(
                <option value={selectValue} key={`duration_${selectValue}`}>
                    {selectValue} минут
                </option>
            );
        }
        return options;
    }, [selectValue, defaultSelectValues]);

    return (
        <CustomModal
            show={show}
            handleClose={() => setShow(false)}
            title={`${specialist.name} - ${patientName} ${patientType} ${dayOfWeek} ${dateString} ${getTimeStringFromDate(startDt)} - ${getTimeStringFromDate(endDt)}`}
            primaryBtnDisabled={!isNewScheduleIntervalValid(appointment, scheduleWithoutCurrentElem, scheduleWithoutCurrentElem, workSchedule.intervals)}
            handlePrimaryBtnClick={onSubmit}
            primaryBtnText={'Сохранить'}
        >
            <div className="d-flex flex-column align-items-center justify-content-center w-100 h-100 gap-2">
                <div className="d-flex w-100 align-items-center" style={{ gap: "1rem", whiteSpace: "nowrap" }}>
                    <label>Начало занятия</label>
                    <InputGroup hasValidation>
                        <FormControl
                            type={'time'}
                            value={getTimeStringFromDate(appointment.start)}
                            name={'start'}
                            onChange={async (e) => {
                                await handleInputChange(e);
                            }}
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
                            value={selectValue}
                            onChange={async (e) => await handleSelectInputChange(e)}
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
                    <FormSelect
                        name={'patientId'}
                        isInvalid={['', null, undefined].includes(appointment.patientId)}
                        onChange={async (e) => {
                            await handleInputChange(e);
                        }}
                        value={appointment.patientId}
                    >
                        {Object.entries(children).map(([childId, childName]) => (
                            <option value={childId} key={`${day}_interval_${recordIndex}_${childId}`}>
                                {childName}
                            </option>
                        ))}
                    </FormSelect>
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
                        {Object.entries(constants.listFieldValues.appointment.idByCode).map(([code, id]) => (
                            <option value={code} key={`${day}_interval_${recordIndex}_${code}_opt`}>
                                {code}
                            </option>
                        ))}
                    </FormSelect>
                </InputGroup>
                <Alert 
                    variant="warning"
                    show={status === 'replace'}
                >
                    {children[schedule[0].old_patient]} заменен на {patientName}
                </Alert>
            </div>          
            <div className="d-flex align-items-left w-100 h-100 gap-2">
                <Button 
                    variant="warning" 
                    onClick={onModalEditBtnClick} 
                    className={'mt-3'} 
                    style={{paddingRight: "1rem"}}
                >
                    Перенести
                </Button>
                <Button variant="danger" onClick={onDeleteBtnClick} className={'mt-3'}>Удалить</Button>
            </div>
        </CustomModal>
    );
};

export default EditAppointmentModal;