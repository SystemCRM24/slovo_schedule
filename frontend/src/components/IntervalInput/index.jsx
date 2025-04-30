import React from 'react';
import {FormControl, InputGroup} from "react-bootstrap";
import {getTimeStringFromDate} from "../../utils/dates.js";

const IntervalInput = ({interval, onChange, isEndInvalid}) => {
    return (
        <>
            <InputGroup style={{width: "50%"}}>
                <FormControl
                    type={'time'}
                    value={getTimeStringFromDate(interval.start)}
                    name={'start'}
                    onChange={onChange}
                    style={{textAlign: "center"}}
                    required
                    isInvalid={!interval.start}
                />
            </InputGroup>
            <span>-</span>
            <InputGroup style={{width: "50%"}}>
                <FormControl
                    type={'time'}
                    value={getTimeStringFromDate(interval?.end)}
                    name={'end'}
                    onChange={onChange}
                    style={{textAlign: "center",}}
                    disabled={!interval?.start}
                    min={getTimeStringFromDate(interval?.start)}
                    required
                    isInvalid={isEndInvalid}
                />
            </InputGroup>
        </>
    );
};

export default IntervalInput;