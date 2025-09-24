<script setup>
import { useAlertStore } from '@/stores/alert'
const store = useAlertStore()
</script>

<template>
    <Transition name="alert" appear>
        <div v-if="store.visibility" class="alert-container">
            <div
                v-if="store.alertType === 0"
                @click="store.visibility = false"
                class="alert alert-success"
                role="alert"
            >
                <div class="alert-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 12l2 2 4-4"/>
                        <circle cx="12" cy="12" r="10"/>
                    </svg>
                </div>
                <div class="alert-content">
                    <div class="alert-message">{{ store.alertText }}</div>
                </div>
                <button @click="store.visibility = false" class="alert-close">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>

            <div
                v-else-if="store.alertType === 1"
                @click="store.visibility = false"
                class="alert alert-error"
                role="alert"
            >
                <div class="alert-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="15" y1="9" x2="9" y2="15"/>
                        <line x1="9" y1="9" x2="15" y2="15"/>
                    </svg>
                </div>
                <div class="alert-content">
                    <div class="alert-message">{{ store.alertText }}</div>
                </div>
                <button @click="store.visibility = false" class="alert-close">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
        </div>
    </Transition>
</template>

<style scoped>
.alert-container {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    max-width: 400px;
    min-width: 200px;
    width: auto;
}

.alert {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    border-radius: 10px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1), 0 3px 8px rgba(0, 0, 0, 0.05);
    backdrop-filter: blur(10px);
    cursor: pointer;
    transition: all 0.3s ease;
    border: 1px solid rgba(255, 255, 255, 0.2);
    width: fit-content;
    margin: 0 auto;
}

.alert:hover {
    transform: translateY(-2px);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15), 0 6px 15px rgba(0, 0, 0, 0.08);
}

.alert-success {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.95) 0%, rgba(21, 128, 61, 0.95) 100%);
    color: white;
    border-color: rgba(34, 197, 94, 0.3);
}

.alert-error {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.95) 0%, rgba(185, 28, 28, 0.95) 100%);
    color: white;
    border-color: rgba(239, 68, 68, 0.3);
}

.alert-icon {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.alert-icon svg {
    width: 100%;
    height: 100%;
}

.alert-content {
    flex: 1;
    min-width: 0;
}

.alert-message {
    font-size: 14px;
    line-height: 1.4;
    opacity: 0.95;
    word-wrap: break-word;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 300px;
}

.alert-close {
    flex-shrink: 0;
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
    padding: 3px;
    border-radius: 5px;
    transition: all 0.2s ease;
    opacity: 0.7;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.alert-close:hover {
    opacity: 1;
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.1);
}

.alert-close svg {
    width: 16px;
    height: 16px;
}

/* Animation transitions */
.alert-enter-active {
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.alert-leave-active {
    transition: all 0.3s ease-in;
}

.alert-enter-from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px) scale(0.9);
}

.alert-leave-to {
    opacity: 0;
    transform: translateX(-50%) translateY(-10px) scale(0.95);
}

/* Responsive design */
@media (max-width: 768px) {
    .alert-container {
        top: 10px;
        left: 10px;
        right: 10px;
        transform: none;
        max-width: none;
        min-width: auto;
    }

    .alert {
        padding: 10px 12px;
        gap: 8px;
        width: 100%;
        margin: 0;
    }

    .alert-message {
        font-size: 13px;
        white-space: normal;
        max-width: none;
    }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .alert {
        border-color: rgba(255, 255, 255, 0.1);
    }

    .alert-success {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.9) 0%, rgba(21, 128, 61, 0.9) 100%);
    }

    .alert-error {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.9) 0%, rgba(185, 28, 28, 0.9) 100%);
    }
}
</style>