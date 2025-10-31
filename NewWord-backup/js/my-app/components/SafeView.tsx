// components/SafeView.tsx
import React from 'react';
import { View, Text, type ViewProps } from 'react-native';

export default function SafeView({ children, ...props }: ViewProps) {
  const wrapped = React.Children.map(children, (child) => {
    if (typeof child === 'string' || typeof child === 'number') {
      return <Text>{child}</Text>;
    }
    return child;
  });
  return <View {...props}>{wrapped}</View>;
}
