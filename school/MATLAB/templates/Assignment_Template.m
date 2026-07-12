%% Assignment Template
% Course: <COURSE>
% Assignment: <TITLE>
% Author: <Your Name>
% Date: <YYYY-MM-DD>
% Purpose: <Short description>

%% Setup
clear; clc; close all;

%% Parameters
k = 120;  % N/m
m = 2.5;  % kg
x0 = 0.02; v0 = 0;

%% Computation
omega = sqrt(k/m);
t = linspace(0, 5, 1001);
x = x0*cos(omega*t) + (v0/omega)*sin(omega*t);

%% Plot
figure; plot(t, x, "LineWidth", 1.2);
xlabel("Time (s)"); ylabel("Displacement (m)");
title("Mass-Spring Response"); grid on;

%% Verification
fprintf('omega = %.3f rad/s\n', omega);