import React from 'react';
import { View, Text, type ViewProps } from 'react-native';
import { useThemeColor } from '@/hooks/useThemeColor';

export type ThemedViewProps = ViewProps & {
  lightColor?: string;
  darkColor?: string;
  children?: React.ReactNode;
};

export function ThemedView({
  style,
  lightColor,
  darkColor,
  children,
  ...otherProps
}: ThemedViewProps) {
  const backgroundColor = useThemeColor({ light: lightColor, dark: darkColor }, 'background');

  const wrappedChildren = React.Children.map(children, (child) => {
    if (typeof child === 'string' || typeof child === 'number') {
      return <Text>{child}</Text>;
    }
    return child;
  });

  return (
    <View style={[{ backgroundColor }, style]} {...otherProps}>
      {wrappedChildren}
    </View>
  );
}
