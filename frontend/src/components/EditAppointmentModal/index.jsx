import React, {useCallback, useMemo, useState} from "react";
import CustomModal from "../ui/Modal";
import {Button, FormControl, FormSelect, InputGroup} from "react-bootstrap";

import {useDayContext} from "../../contexts/Day/provider";
import useSchedules from "../../hooks/useSchedules";
import useSpecialist from "../../hooks/useSpecialist.js";
import {getDateWithTime, getTimeStringFromDate, isIntervalValid, isNewScheduleIntervalValid} from "../../utils/dates.js";
import {useChildrenContext} from "../../contexts/Children/provider.jsx";
import apiClient, {constants} from "../../api/index.js";


const EditAppointmentModal = ({id, show, setShow, startDt, endDt, patientId, patientType, status}) => {
    const {specialistId, specialist} = useSpecialist();
    const [appointment, setAppointment] = useState(
        {
            id: id, status: status, patientId: patientId, patientType: patientType, start: startDt, end: endDt,
            specialist: specialistId,
        }
    );
    const {
        schedule, generalSchedule,
        setGeneralSchedule, workSchedule
    } = useSchedules();
    const patients = useChildrenContext();
    const patientName = useMemo(() => {
        return patients?.[patientId];
    }, [patientId, patients]);
    const day = useDayContext();
    const children = useChildrenContext();
    const dayOfWeek = day.toLocaleString('ru-RU', {weekday: 'long'});
    const dateString = day.toLocaleDateString();

    const statuses = useMemo(() => {
        return {
            confirmed: "Подтверждено",
            booked: "Забронировано",
        }
    }, []);

    const [record, recordIndex] = useMemo(
        () => {
            let index = -1;
            for (const record of schedule) {
                index++;
                if (record.start.getTime() === startDt.getTime() && record.end.getTime() === endDt.getTime()) {
                    return [record, index];
                }
            }
            return [{}, -1];
        },
        [schedule, startDt, endDt]
    );

    const onDeleteBtnClick = useCallback(
        () => {
            (async () => {
                await apiClient.deleteAppointment(id)
                setShow(false);
                const newSchedule = schedule.filter((item, index) => index !== recordIndex);
                setGeneralSchedule({
                    ...generalSchedule,
                    [specialistId]: {
                        ...generalSchedule[specialistId],
                        [day]: newSchedule,
                    }
                })
            })();
        },
        [id, setShow, schedule, setGeneralSchedule, generalSchedule, specialistId, day, recordIndex]
    );

    const scheduleWithoutCurrentElem = useMemo(() => {
        return schedule.filter((value, index) => index !== recordIndex);
    }, [recordIndex, schedule]);

    const handleInputChange = async (e) => {
        let value;
        if (['start', 'end'].includes(e.target.name)) {
            const [hoursString, minutesString] = e.target.value.split(':');
            const hours = parseInt(hoursString);
            const minutes = parseInt(minutesString);
            value = getDateWithTime(day, hours, minutes);
        } else {
            value = e.target.value;
        }
        await onChange(e.target.name, value);
    }

    const onChange = async (attrName, value) => {
        setAppointment({...appointment, [attrName]: value});
    }

    const onSubmit = async () => {
        const newRecord = {
            id: appointment.id,
            start: appointment.start,
            end: appointment.end,
            patient: appointment.patientId,
            code: appointment.patientType,
            status: appointment.status,
        }
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
    }


    return (
        <CustomModal
            show={show}
            handleClose={() => setShow(false)}
            title={
                `${specialist.name} - ${patientName} ${patientType} ${dayOfWeek} ${dateString}
             ${getTimeStringFromDate(startDt)} - ${getTimeStringFromDate(endDt)}`
            }
            primaryBtnDisabled={!isNewScheduleIntervalValid(appointment, scheduleWithoutCurrentElem, scheduleWithoutCurrentElem, workSchedule.intervals)}
            handlePrimaryBtnClick={onSubmit}
            primaryBtnText={'Сохранить'}
        >
            <div className="d-flex flex-column align-items-center justify-content-center w-100 h-100 gap-2">
                <InputGroup hasValidation>
                    <FormControl
                        type={'time'}
                        value={getTimeStringFromDate(appointment.start)}
                        name={'start'}
                        onChange={async (e) => {
                            await handleInputChange(e);
                        }}
                        style={{textAlign: "center"}}
                        required
                        isInvalid={
                            !appointment.start ||
                            (
                                !!appointment.start
                                && !isNewScheduleIntervalValid(appointment, scheduleWithoutCurrentElem, scheduleWithoutCurrentElem, workSchedule.intervals)
                            )
                        }
                    />
                </InputGroup>
                <span>-</span>
                <InputGroup hasValidation className={'mb-4'}>
                    <FormControl
                        type={'time'}
                        value={getTimeStringFromDate(appointment.end)}
                        name={'end'}
                        onChange={async (e) => {
                            await handleInputChange(e);
                        }}
                        style={{textAlign: "center",}}
                        disabled={!appointment.start}
                        min={getTimeStringFromDate(appointment.start)}
                        required
                        isInvalid={
                            appointment.start !== undefined &&
                            (
                                !isIntervalValid(appointment) ||
                                !isNewScheduleIntervalValid(appointment, scheduleWithoutCurrentElem, scheduleWithoutCurrentElem, workSchedule.intervals)
                            )
                        }
                    />
                </InputGroup>
                <InputGroup hasValidation>
                    <FormSelect
                        name={'patientId'}
                        isInvalid={['', null, undefined].includes(appointment.patientId)}
                        onChange={async (e) => {
                            await handleInputChange(e);
                        }}
                        value={appointment.patientId}
                    >
                        {Object.entries(children).map(([childId, childName]) => {
                            return (
                                <option value={childId} key={`${day}_interval_${recordIndex}_${childId}`}>
                                    {childName}
                                </option>
                            );
                        })}
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
                        {Object.entries(constants.listFieldValues.appointment.idByCode).map(([code, id]) => {
                            return (
                                <option value={code} key={`${day}_interval_${recordIndex}_${code}_opt`}>
                                    {code}
                                </option>
                            );
                        })}
                    </FormSelect>
                </InputGroup>
                <InputGroup hasValidation>
                    <FormSelect
                        name={'status'}
                        isInvalid={['', null, undefined].includes(appointment.status)}
                        onChange={async (e) => {
                            await handleInputChange(e);
                        }}
                        value={appointment.status}
                    >
                        {Object.entries(statuses).map(([code, label]) => {
                            return (
                                <option value={code} key={`${day}_interval_${recordIndex}_${code}_${label}_opt`}>
                                    {label}
                                </option>
                            );
                        })}
                    </FormSelect>
                </InputGroup>
                <Button
                    variant="danger"
                    onClick={onDeleteBtnClick}
                    className={'mt-3'}
                >
                    Удалить
                </Button>
            </div>
        </CustomModal>
    );
}

export default React.memo(EditAppointmentModal);