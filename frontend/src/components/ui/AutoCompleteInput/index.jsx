import { useMemo } from 'react';
import { Form, InputGroup } from 'react-bootstrap';
import Select from 'react-select';
import "./AutoCompleteInput.css"

function AutoCompleteInput({ options, onChange, value, name, isInvalid }) {
    const selectOptions = useMemo(() => 
        Object.entries(options).map(([id, label]) => ({
            value: id,
            label
        })), 
        [options]
    );

    const selectedOption = useMemo(() => 
        value && options[value] 
            ? { value, label: options[value] } 
            : null, 
        [value, options]
    );

    const handleChange = (selected) => {
        if (onChange) {
            onChange({
                target: {
                    name,
                    value: selected ? selected.value : ''
                }
            });
        }
    };

    return (
        <InputGroup hasValidation>
            <Form.Control
                as={Select}
                options={selectOptions}
                value={selectedOption}
                onChange={handleChange}
                placeholder="Выберите клиента"
                name={name}
                isInvalid={isInvalid}
                isSearchable
                className='p-0'
                classNamePrefix="react-select"
                noOptionsMessage={() => 'Нет подходящих клиента'}
            />
        </InputGroup>
    );
}

export default AutoCompleteInput;