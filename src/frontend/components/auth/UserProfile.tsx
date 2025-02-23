import React from 'react';
import { useAuth } from '../../hooks/useAuth';

const UserProfile: React.FC = () => {
    const { user, logout } = useAuth();

    if (!user) {
        return null;
    }

    return (
        <div className="user-profile">
            <h2>Profile</h2>
            <div className="profile-info">
                <p><strong>Email:</strong> {user.email}</p>
                <p><strong>Username:</strong> {user.username}</p>
                <p><strong>Full Name:</strong> {user.fullName}</p>
                <p><strong>Tier:</strong> {user.tier}</p>
            </div>
            <button onClick={logout}>Logout</button>
        </div>
    );
};

export default UserProfile; 