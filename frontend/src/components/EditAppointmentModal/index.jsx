import React, {useCallback, useMemo, useState} from "react";
import CustomModal from "../ui/Modal";
import {Button, FormControl, FormSelect, InputGroup} from "react-bootstrap";

import {useDayContext} from "../../contexts/Day/provider";
import useSchedules from "../../hooks/useSchedules";
import useSpecialist from "../../hooks/useSpecialist.js";
import {getDateWithTime, getTimeStringFromDate, isIntervalValid, isScheduleValid} from "../../utils/dates.js";


const EditAppointmentModal = ({show, setShow, startDt, endDt, patientName, patientType, status}) => {
    const [appointment, setAppointment] = useState(
        {status: status, patientName: patientName, patientType: patientType, start: startDt, end: endDt}
    );
    const {specialistId, specialist} = useSpecialist();
    const {
        schedule, generalSchedule,
        setGeneralSchedule, workSchedule
    } = useSchedules();
    const day = useDayContext();
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
            setShow(false);
            const newSchedule = schedule.filter((item, index) => index !== recordIndex);
            setGeneralSchedule({
                ...generalSchedule,
                [specialistId]: {
                    ...generalSchedule[specialistId],
                    [day]: newSchedule,
                }
            })
        },
        [setShow, recordIndex, schedule, setGeneralSchedule, generalSchedule, specialistId]
    );

    const scheduleWithoutCurrentElem = useMemo(() => {
        return schedule.filter((value, index) => index !== recordIndex);
    }, [recordIndex, schedule]);
    console.log(schedule, scheduleWithoutCurrentElem)

    const children = useMemo(() => {
        return [
            'Тестовый П.',
            "Тестовый2 П.",
            "Иванов. И."
        ];
    }, []);

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
            start: appointment.start,
            end: appointment.end,
            patient: {
                name: appointment.patientName,
                type: appointment.patientType,
            },
            status: appointment.status,
        }
        const newSchedule = schedule.map((item, index) => {
            if (index === recordIndex) {
                return newRecord
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


    return (
        <CustomModal
            show={show}
            handleClose={() => setShow(false)}
            title={
                `${specialist.name} - ${patientName} ${patientType} ${dayOfWeek} ${dateString}
             ${getTimeStringFromDate(startDt)} - ${getTimeStringFromDate(endDt)}`
            }
            primaryBtnDisabled={!isScheduleValid(appointment, scheduleWithoutCurrentElem, scheduleWithoutCurrentElem, workSchedule)}
            handlePrimaryBtnClick={onSubmit}
            primaryBtnText={'Сохранить'}
        >
            <div className="d-flex flex-column align-items-center justify-content-center w-100 h-100 gap-2">
                <InputGroup hasValidation>
                    <FormControl
                        type={'time'}
                        key={`${day}_interval_${recordIndex}_start`}
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
                                && !isScheduleValid(appointment, scheduleWithoutCurrentElem, scheduleWithoutCurrentElem, workSchedule)
                            )
                        }
                    />
                </InputGroup>
                <span>-</span>
                <InputGroup hasValidation className={'mb-4'}>
                    <FormControl
                        type={'time'}
                        key={`${day}_interval_${recordIndex}_end`}
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
                                !isScheduleValid(appointment, scheduleWithoutCurrentElem, scheduleWithoutCurrentElem, workSchedule)
                            )
                        }
                    />
                </InputGroup>
                <InputGroup hasValidation>
                    <FormSelect
                        name={'patientName'}
                        isInvalid={['', null, undefined].includes(appointment.patientName)}
                        onChange={async (e) => {
                            await handleInputChange(e);
                        }}
                        value={appointment.patientName}
                    >
                        {children.map(child => {
                            return (
                                <option value={child} key={`${day}_interval_${recordIndex}_${child}`}>
                                    {child}
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
                        {specialist.departments.map(code => {
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