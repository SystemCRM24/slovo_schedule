import React, { useContext, useEffect, useMemo, useState } from "react";
import {Button, Modal} from "react-bootstrap";

import { AppContext } from "../../../contexts/App/context";


export default function CustomModal({
    show,
    handleClose, 
    handlePrimaryBtnClick, 
    primaryBtnText,
    primaryBtnDisabled = true,
    title,
    size = 'xl',
    children
}) {
    const [isMinimized, setIsMinimized] = useState(false);
    const {modalWindowCount, decreaseModalCount} = useContext(AppContext);

    const headerStyle = useMemo(
        () => {
            let style = {};
            if (isMinimized) {
                style = {
                    width: '400px',
                    height: '200px',
                    position: 'fixed',
                    top: 'auto', 
                    right: '20px',
                    left: 'auto',
                    bottom: '20px'
                }
            }
            return style;
        },
        [isMinimized]
    );

    const bodyStyle = useMemo(
        () => {
            let style = {};
            if (isMinimized) {
                style = {
                    display: 'none'
                };
            }
            return style
        },
        [isMinimized]
    );

    const onModalHide = () => {
        decreaseModalCount();
        handleClose();
        setIsMinimized(false);
    }

    const onPrimaryBtnClick = () => {
        decreaseModalCount();
        handlePrimaryBtnClick();
    }

    const modalTitle = useMemo(
        () => {
            if ( isMinimized && title.length > 50) {
                return title.slice(0, 50) + ' ...';
            };
            return title;
        },
        [title, isMinimized]
    )

    return (
        <Modal 
            show={show} 
            onHide={onModalHide} 
            size={size} 
            centered
            backdrop={!isMinimized}
            enforceFocus={!isMinimized}
            animation={!isMinimized}
            style={headerStyle}
        >
            <Modal.Header 
                closeButton
                style={{backgroundColor: "AEE9FF"}}
            >
                <div className="d-flex justify-content-between" style={{width: '100%'}}>
                    <Modal.Title>{modalTitle}</Modal.Title>
                    <Button
                        variant="link"
                        style={{color: 'gray'}}
                        onClick={() => setIsMinimized(!isMinimized)}
                        disabled={modalWindowCount > 1}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-dash-lg" viewBox="0 0 16 16">
                            <path fill-rule="evenodd" d="M2 8a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11A.5.5 0 0 1 2 8"/>
                        </svg>
                    </Button>
                </div>
            </Modal.Header>
            <Modal.Body style={bodyStyle}>
                {children}
            </Modal.Body>
            <Modal.Footer style={bodyStyle}>
                <Button variant="outline-dark" onClick={onModalHide}>
                    Закрыть
                </Button>
                {(primaryBtnText && handlePrimaryBtnClick) &&
                    <Button variant="success" onClick={onPrimaryBtnClick} disabled={primaryBtnDisabled}>
                        {primaryBtnText}
                    </Button>}
            </Modal.Footer>
        </Modal>
    );
}
